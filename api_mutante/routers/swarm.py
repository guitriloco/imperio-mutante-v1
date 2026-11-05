from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api_mutante.agents.swarm_orchestrator import swarm_orchestrator

router = APIRouter(prefix="/v1/swarm", tags=["Multi-Agent Swarm & Self-Healing"])

class SelfHealingRequest(BaseModel):
    script_path: str = Field(..., description="Caminho do arquivo Python para executar e auto-curar em caso de falha")
    max_healing_cycles: int = Field(default=3, ge=1, le=5, description="Máximo de tentativas de regeneração de patch")

class SelfHealingResponse(BaseModel):
    success: bool
    script_path: str
    healing_cycles_used: int
    healing_history: list
    final_stdout: str
    final_stderr: str

@router.post(
    "/self-heal",
    response_model=SelfHealingResponse,
    status_code=status.HTTP_200_OK,
    summary="Executa código e aciona enxame multi-agente para auto-cura se houver falhas"
)
async def trigger_self_healing(request: SelfHealingRequest) -> SelfHealingResponse:
    try:
        result = await swarm_orchestrator.execute_task_with_healing(
            script_path=request.script_path,
            max_healing_cycles=request.max_healing_cycles
        )
        return SelfHealingResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha no loop de auto-cura do enxame: {str(e)}"
        )
