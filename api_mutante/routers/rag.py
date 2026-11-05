from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from api_mutante.rag_engine import rag_engine

router = APIRouter(prefix="/v1/rag", tags=["RAG & Semantic Search"])

class RAGSearchRequest(BaseModel):
    query: str = Field(..., description="Pergunta ou termo para busca semântica")
    top_k: int = Field(default=3, ge=1, le=10, description="Quantidade de resultados a retornar")

class RAGSearchResultItem(BaseModel):
    score: float
    doc_id: str
    title: Optional[str]
    source_file: Optional[str]
    summary: Optional[str]
    key_takeaways: List[str] = []
    actionable_insights: List[str] = []
    tags: List[str] = []

class RAGSearchResponse(BaseModel):
    success: bool
    query: str
    total_matches: int
    results: List[RAGSearchResultItem]

@router.post(
    "/search",
    response_model=RAGSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Busca semântica por similaridade vetorial via Gemini Embeddings"
)
async def semantic_search(request: RAGSearchRequest) -> RAGSearchResponse:
    try:
        matches = await rag_engine.search(query=request.query, top_k=request.top_k)
        return RAGSearchResponse(
            success=True,
            query=request.query,
            total_matches=len(matches),
            results=[RAGSearchResultItem(**m) for m in matches]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na busca vetorial: {str(e)}"
        )

@router.post(
    "/reindex",
    summary="Força a geração e atualização dos embeddings de todos os documentos"
)
async def reindex_documents():
    try:
        count = await rag_engine.index_all_documents(force=True)
        return {"success": True, "indexed_documents": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na indexação vetorial: {str(e)}"
        )
