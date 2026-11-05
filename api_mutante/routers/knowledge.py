import json
import re
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import pypdf

from api_mutante.core.config import settings
from api_mutante.core.gemini_service import gemini_service
from api_mutante.prompts_manager import prompts_manager

router = APIRouter(prefix="/v1/knowledge", tags=["Knowledge"])

# Caminhos absolutos
KNOWLEDGE_DIR = Path("C:/Users/Administrator/ImperioMutante/02_CONHECIMENTO")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class IngestRequest(BaseModel):
    filename: Optional[str] = Field(default=None, description="Nome do arquivo específico para ingerir. Se omitido, processa todos.")
    model: Optional[str] = Field(default="gemini-2.5-flash", description="Modelo do Gemini")

class IngestedItem(BaseModel):
    filename: str
    status: str
    data_file: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None

class IngestResponse(BaseModel):
    success: bool
    processed_count: int
    items: List[IngestedItem]

def extract_text_from_file(file_path: Path) -> str:
    """Extrai texto de arquivos .txt, .md e .pdf."""
    suffix = file_path.suffix.lower()
    
    if suffix in [".txt", ".md", ".markdown", ".csv", ".json"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    
    elif suffix == ".pdf":
        text_parts = []
        reader = pypdf.PdfReader(str(file_path))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted)
        return "\n".join(text_parts)
    
    else:
        raise ValueError(f"Formato de arquivo '{suffix}' não suportado.")

def parse_json_from_gemini(raw_text: str) -> dict:
    """Higieniza e converte blocos markdown retornados pelo modelo em dict JSON."""
    cleaned = raw_text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if match:
        cleaned = match.group(1).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        return {
            "title": "Documento Ingerido",
            "summary": raw_text,
            "key_takeaways": [],
            "actionable_insights": [],
            "tags": ["auto-ingest"]
        }

@router.get(
    "/documents",
    summary="Lista todos os documentos indexados em 02_CONHECIMENTO"
)
async def list_documents():
    index_file = DATA_DIR / "index.json"
    if not index_file.exists():
        return {}
    try:
        with open(index_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao ler índice: {str(e)}"
        )

@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingere e sintetiza documentos de 02_CONHECIMENTO em JSON estruturado"
)
async def ingest_knowledge(request: IngestRequest) -> IngestResponse:
    if not KNOWLEDGE_DIR.exists():
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    # Identifica arquivos alvos
    if request.filename:
        target_path = KNOWLEDGE_DIR / request.filename
        if not target_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Arquivo '{request.filename}' não encontrado em 02_CONHECIMENTO."
            )
        target_files = [target_path]
    else:
        target_files = [
            f for f in KNOWLEDGE_DIR.glob("*")
            if f.is_file() and f.suffix.lower() in [".txt", ".md", ".pdf", ".markdown"]
        ]

    if not target_files:
        return IngestResponse(
            success=True,
            processed_count=0,
            items=[]
        )

    results: List[IngestedItem] = []
    index_file = DATA_DIR / "index.json"
    
    # Carrega índice existente
    index_data = {}
    if index_file.exists():
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        except Exception:
            index_data = {}

    for file_path in target_files:
        try:
            raw_content = extract_text_from_file(file_path)
            if not raw_content.strip():
                results.append(IngestedItem(filename=file_path.name, status="skipped", error="Arquivo vazio"))
                continue

            # Renderiza prompt usando o PromptsManager
            rendered_prompt, system_inst = prompts_manager.render(
                "knowledge_summarizer",
                content=raw_content[:40000] # Limite de segurança de caracteres
            )

            # Executa inferência assíncrona
            gemini_out = await gemini_service.generate_async(
                prompt=rendered_prompt,
                model=request.model or settings.DEFAULT_MODEL,
                system_instruction=system_inst
            )

            parsed_data = parse_json_from_gemini(gemini_out)
            parsed_data["source_file"] = file_path.name

            # Salva arquivo JSON estruturado
            output_name = f"{file_path.stem}.json"
            output_path = DATA_DIR / output_name
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)

            # Atualiza índice global
            index_data[file_path.name] = {
                "title": parsed_data.get("title", file_path.stem),
                "summary": parsed_data.get("summary", ""),
                "tags": parsed_data.get("tags", []),
                "json_path": str(output_path)
            }

            results.append(IngestedItem(
                filename=file_path.name,
                status="success",
                data_file=str(output_path),
                title=parsed_data.get("title")
            ))

        except Exception as e:
            results.append(IngestedItem(
                filename=file_path.name,
                status="error",
                error=str(e)
            ))

    # Salva índice consolidado
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    return IngestResponse(
        success=True,
        processed_count=len([r for r in results if r.status == "success"]),
        items=results
    )
