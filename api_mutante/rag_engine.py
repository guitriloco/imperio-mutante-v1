import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

from api_mutante.core.config import settings
from api_mutante.core.gemini_service import gemini_service

DATA_DIR = Path(__file__).resolve().parent / "data"
CACHE_FILE = DATA_DIR / "embeddings_cache.json"

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calcula a similaridade de cosseno pura sem dependências pesadas."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)

class RAGEngine:
    """Motor de Busca Semântica e RAG nativo usando embeddings da Gemini API."""

    def __init__(self, embedding_model: str = "gemini-embedding-001"):
        self.embedding_model = embedding_model
        self._cache: Dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self):
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save_cache(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, indent=2, ensure_ascii=False)

    async def get_embedding(self, text: str) -> List[float]:
        """Gera embedding vetorial via Gemini SDK."""
        response = await gemini_service.client.aio.models.embed_content(
            model=self.embedding_model,
            contents=[text]
        )
        return response.embeddings[0].values

    async def index_all_documents(self, force: bool = False) -> int:
        """Gera embeddings para todos os documentos JSON estruturados em api_mutante/data."""
        if not DATA_DIR.exists():
            return 0

        indexed_count = 0
        json_files = [
            f for f in DATA_DIR.glob("*.json")
            if f.name not in ["index.json", "embeddings_cache.json"]
        ]

        for file in json_files:
            file_key = file.name
            if not force and file_key in self._cache:
                continue

            try:
                with open(file, "r", encoding="utf-8") as f:
                    doc = json.load(f)

                # Monta contexto semântico consolidado (com conversão resiliente de tipos)
                def clean_list(val):
                    if isinstance(val, list):
                        return " ".join(str(x) for x in val)
                    return str(val)

                context_parts = [
                    f"Título: {doc.get('title', '')}",
                    f"Resumo: {doc.get('summary', '')}",
                    f"Pontos-chave: {clean_list(doc.get('key_takeaways', []))}",
                    f"Insights acionáveis: {clean_list(doc.get('actionable_insights', []))}",
                    f"Tags: {clean_list(doc.get('tags', []))}"
                ]
                searchable_text = "\n".join(context_parts)

                vector = await self.get_embedding(searchable_text)

                self._cache[file_key] = {
                    "source_file": doc.get("source_file", file.stem),
                    "title": doc.get("title", file.stem),
                    "summary": doc.get("summary", ""),
                    "key_takeaways": doc.get("key_takeaways", []),
                    "actionable_insights": doc.get("actionable_insights", []),
                    "tags": doc.get("tags", []),
                    "vector": vector
                }
                indexed_count += 1
            except Exception as e:
                print(f"[RAG] Erro ao indexar {file.name}: {e}")

        if indexed_count > 0 or force:
            self._save_cache()

        return indexed_count

    async def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Busca os documentos mais similares semanticamente com a consulta."""
        # Garante que a base está indexada
        if not self._cache:
            await self.index_all_documents()

        if not self._cache:
            return []

        query_vector = await self.get_embedding(query)
        scored_results = []

        for doc_key, data in self._cache.items():
            doc_vec = data.get("vector")
            if not doc_vec:
                continue
            score = cosine_similarity(query_vector, doc_vec)
            scored_results.append({
                "score": round(score, 4),
                "doc_id": doc_key,
                "title": data.get("title"),
                "source_file": data.get("source_file"),
                "summary": data.get("summary"),
                "key_takeaways": data.get("key_takeaways", []),
                "actionable_insights": data.get("actionable_insights", []),
                "tags": data.get("tags", [])
            })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

rag_engine = RAGEngine()
