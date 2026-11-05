from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from api_mutante.core.gemini_service import gemini_service
from api_mutante.core.config import settings

router = APIRouter(prefix="/v1", tags=["Generate"])

class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Prompt a ser processado pelo modelo")
    model: str | None = Field(default=None, description="Modelo do Gemini (default: gemini-2.5-flash)")
    system_instruction: str | None = Field(default=None, description="Diretriz de sistema opcional")

class GenerateResponse(BaseModel):
    success: bool
    content: str
    model_used: str

@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Gera conteúdo assíncrono via Gemini API"
)
async def generate_endpoint(request: GenerateRequest) -> GenerateResponse:
    try:
        model_to_use = request.model or settings.DEFAULT_MODEL
        result = await gemini_service.generate_async(
            prompt=request.prompt,
            model=model_to_use,
            system_instruction=request.system_instruction
        )
        return GenerateResponse(
            success=True,
            content=result,
            model_used=model_to_use
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na inferência do modelo: {str(e)}"
        )
