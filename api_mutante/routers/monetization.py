from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from api_mutante.core.security import api_key_manager, TIER_LIMITS

router = APIRouter(prefix="/v1/monetization", tags=["Monetization & API Keys"])

class CreateKeyRequest(BaseModel):
    owner_name: str = Field(..., description="Nome do cliente ou empresa compradora")
    tier: str = Field(default="FREE", description="Nível de serviço: FREE, PRO ou ENTERPRISE")

class CreateKeyResponse(BaseModel):
    success: bool
    api_key: str
    owner: str
    tier: str
    rate_limit_rpm: int
    allowed_models: List[str]

class KeyStatusResponse(BaseModel):
    owner: str
    tier: str
    total_requests: int
    is_active: bool
    created_at: str

@router.post(
    "/keys/generate",
    response_model=CreateKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Emite uma nova chave de API com limites baseados em Tier para monetização"
)
async def generate_api_key_endpoint(payload: CreateKeyRequest) -> CreateKeyResponse:
    try:
        raw_key, meta = api_key_manager.generate_key(
            owner_name=payload.owner_name,
            tier=payload.tier
        )
        tier_cfg = TIER_LIMITS[meta["tier"]]
        return CreateKeyResponse(
            success=True,
            api_key=raw_key,
            owner=meta["owner"],
            tier=meta["tier"],
            rate_limit_rpm=tier_cfg["rpm"],
            allowed_models=tier_cfg["allowed_models"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Falha ao gerar chave: {str(e)}"
        )

@router.get(
    "/tiers",
    summary="Retorna os planos e limites disponíveis para compra/checkout"
)
async def list_tiers() -> Dict[str, Any]:
    return TIER_LIMITS
