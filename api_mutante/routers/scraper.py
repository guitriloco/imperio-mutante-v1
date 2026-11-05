from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

from api_mutante.services.scraper_service import scraper_service

router = APIRouter(prefix="/v1/research", tags=["Autonomous Research Agent"])

class ScrapeResearchRequest(BaseModel):
    url: str = Field(..., description="URL pública para pesquisa e raspagem de dados")
    topic: Optional[str] = Field(default=None, description="Tópico de foco para direcionar a síntese de inteligência")
    auto_index_rag: bool = Field(default=True, description="Se deve indexar o conteúdo gerado imediatamente no RAG")

class ScrapeResearchResponse(BaseModel):
    success: bool
    url: str
    title: str
    saved_file: str
    filename: str
    rag_indexed: bool
    preview_summary: str

@router.post(
    "/scrape-and-ingest",
    response_model=ScrapeResearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Raspa página web, sintetiza inteligência via Gemini e injeta em 02_CONHECIMENTO"
)
async def scrape_and_ingest_endpoint(request: ScrapeResearchRequest) -> ScrapeResearchResponse:
    try:
        result = await scraper_service.research_and_ingest(
            url=request.url,
            topic=request.topic,
            auto_index_rag=request.auto_index_rag
        )
        return ScrapeResearchResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha no agente de pesquisa autônoma: {str(e)}"
        )
