from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api_mutante.services.mass_ingest_service import mass_ingest_pipeline

router = APIRouter(prefix="/v1/mass-ingest", tags=["High-Volume Knowledge ETL"])

class BatchIngestRequest(BaseModel):
    force_rag_reindex: bool = Field(default=True, description="Se deve forçar a regeneração completa de todos os embeddings vetoriais")

class BatchIngestResponse(BaseModel):
    total_files_scanned: int
    successful_extractions: int
    vector_embeddings_generated: int
    records: list

@router.post(
    "/execute",
    response_model=BatchIngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Dispara processamento em lote concorrente de todos os arquivos em 02_CONHECIMENTO"
)
async def trigger_mass_ingest(request: BatchIngestRequest) -> BatchIngestResponse:
    try:
        result = await mass_ingest_pipeline.execute_batch_ingest(
            force_rag_reindex=request.force_rag_reindex
        )
        return BatchIngestResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na execução do pipeline em massa: {str(e)}"
        )
