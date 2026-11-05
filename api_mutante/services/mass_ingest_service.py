import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pypdf
from bs4 import BeautifulSoup

from api_mutante.core.config import settings
from api_mutante.core.gemini_service import gemini_service
from api_mutante.prompts_manager import prompts_manager
from api_mutante.rag_engine import rag_engine, DATA_DIR
from api_mutante.routers.knowledge import KNOWLEDGE_DIR, parse_json_from_gemini

logger = logging.getLogger("api_mutante.mass_ingest")

def extract_text_advanced(file_path: Path) -> str:
    """Extrai texto com suporte para .pdf, .epub, .md e .txt."""
    suffix = file_path.suffix.lower()

    if suffix in [".txt", ".md", ".markdown", ".csv", ".json"]:
        return file_path.read_text(encoding="utf-8", errors="ignore")

    elif suffix == ".pdf":
        text_parts = []
        reader = pypdf.PdfReader(str(file_path))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted)
        return "\n".join(text_parts)

    elif suffix == ".epub":
        try:
            import ebooklib
            from ebooklib import epub
            book = epub.read_epub(str(file_path))
            chapters = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), "html.parser")
                    text = soup.get_text(strip=True)
                    if len(text) > 50:
                        chapters.append(text)
            return "\n\n".join(chapters)
        except Exception as e:
            logger.warning(f"Falha na extração de EPUB ({file_path.name}): {e}")
            return ""

    raise ValueError(f"Formato não suportado: {suffix}")

class HighVolumeIngestionPipeline:
    """Pipeline assíncrono de ETL de alto volume com geração de embeddings vetoriais de 3072-d."""

    def __init__(self, chunk_size_chars: int = 35000, concurrency_limit: int = 3):
        self.chunk_size = chunk_size_chars
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    async def process_single_file(self, file_path: Path) -> Dict[str, Any]:
        """Processa, resume e indexa um documento individual com controle de concorrência."""
        async with self.semaphore:
            raw_text = extract_text_advanced(file_path)
            if not raw_text.strip():
                return {"file": file_path.name, "status": "skipped", "reason": "empty_content"}

            # Síntese Estruturada via Gemini
            prompt, system_inst = prompts_manager.render(
                "knowledge_summarizer",
                content=raw_text[:self.chunk_size]
            )

            model_output = await gemini_service.generate_async(
                prompt=prompt,
                system_instruction=system_inst
            )

            parsed_data = parse_json_from_gemini(model_output)
            parsed_data["source_file"] = file_path.name
            parsed_data["raw_char_count"] = len(raw_text)

            # Persistência do JSON Sintetizado
            dest_json = DATA_DIR / f"{file_path.stem}.json"
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(dest_json, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)

            return {
                "file": file_path.name,
                "status": "success",
                "title": parsed_data.get("title", file_path.stem),
                "dest_json": str(dest_json)
            }

    async def execute_batch_ingest(self, target_dir: Optional[Path] = None, force_rag_reindex: bool = True) -> Dict[str, Any]:
        """Varre o diretório, processa arquivos concorrentemente e sincroniza a base vetorial."""
        scan_dir = target_dir or KNOWLEDGE_DIR
        scan_dir.mkdir(parents=True, exist_ok=True)

        supported_exts = {".txt", ".md", ".pdf", ".epub", ".markdown"}
        raw_files = [f for f in scan_dir.glob("*") if f.is_file() and f.suffix.lower() in supported_exts]

        if not raw_files:
            return {"total_files": 0, "processed": 0, "status": "no_files_found"}

        # Execução concorrente limitada por semáforo
        tasks = [self.process_single_file(f) for f in raw_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_records = []
        for r in results:
            if isinstance(r, dict):
                processed_records.append(r)
            else:
                processed_records.append({"status": "error", "error": str(r)})

        # Atualização do Índice Consolidado
        index_file = DATA_DIR / "index.json"
        index_data = {}
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
            except Exception:
                index_data = {}

        for rec in processed_records:
            if rec.get("status") == "success":
                dest_p = Path(rec["dest_json"])
                try:
                    with open(dest_p, "r", encoding="utf-8") as jf:
                        j_content = json.load(jf)
                    index_data[rec["file"]] = {
                        "title": j_content.get("title", rec["file"]),
                        "summary": j_content.get("summary", ""),
                        "tags": j_content.get("tags", []),
                        "json_path": str(dest_p)
                    }
                except Exception:
                    pass

        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

        # Sincronização e Geração de Embeddings no RAGEngine
        vectors_indexed = 0
        if force_rag_reindex:
            vectors_indexed = await rag_engine.index_all_documents(force=True)

        return {
            "total_files_scanned": len(raw_files),
            "successful_extractions": len([r for r in processed_records if r.get("status") == "success"]),
            "vector_embeddings_generated": vectors_indexed,
            "records": processed_records
        }

mass_ingest_pipeline = HighVolumeIngestionPipeline()
