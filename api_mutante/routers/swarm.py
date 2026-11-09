from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api_mutante.agents.swarm_orchestrator import swarm_orchestrator

router = APIRouter(prefix="/v1/swarm", tags=["Multi-Agent Swarm & Self-Healing"])

# Modelos
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

class PlanRequest(BaseModel):
    task_description: str = Field(..., description="Descrição da missão ou tarefa técnica para decompor")

class PlanResponse(BaseModel):
    success: bool
    task_description: str
    plan: List[Dict[str, Any]]

class AuditRequest(BaseModel):
    code_snippet: str = Field(..., description="Código Python a ser analisado")
    context: Optional[str] = Field(default="", description="Contexto arquitetural do repositório")

class AuditResponse(BaseModel):
    success: bool
    is_valid: bool
    severity: str
    issues: List[str]

class RunTestRequest(BaseModel):
    script_path: str = Field(..., description="Caminho do script a ser executado no subprocesso")

class RunTestResponse(BaseModel):
    success: bool
    exit_code: int
    stdout: str
    stderr: str

class SwarmStatusResponse(BaseModel):
    status: str
    agents: Dict[str, Dict[str, str]]
    healing_engine_active: bool

# Endpoints
@router.get(
    "/status",
    response_model=SwarmStatusResponse,
    summary="Telemetria e status dos agentes do enxame autônomo"
)
async def get_swarm_status() -> SwarmStatusResponse:
    return SwarmStatusResponse(
        status="OPERATIONAL",
        agents={
            "TaskPlannerAgent": {"role": "Decomposição Estratégica", "state": "ONLINE", "model": "gemini-2.5-flash"},
            "CodeAuditorAgent": {"role": "Auditoria de Segurança & Qualidade", "state": "ONLINE", "model": "gemini-2.5-flash"},
            "TestRunnerAgent": {"role": "Subprocess Execution Sandbox", "state": "ONLINE", "model": "native-runtime"},
            "SelfHealingCore": {"role": "Auto-Patching Loop com RAG", "state": "ARMED", "model": "gemini-2.5-flash"}
        },
        healing_engine_active=True
    )

@router.post(
    "/plan",
    response_model=PlanResponse,
    summary="Decompõe uma missão técnica em plano de ação atômico via TaskPlannerAgent"
)
async def plan_mission(request: PlanRequest) -> PlanResponse:
    try:
        plan = await swarm_orchestrator.planner.create_plan(request.task_description)
        return PlanResponse(success=True, task_description=request.task_description, plan=plan)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha no planejador: {str(e)}")

@router.post(
    "/audit",
    response_model=AuditResponse,
    summary="Audita código-fonte Python e detecta vulnerabilidades via CodeAuditorAgent"
)
async def audit_code(request: AuditRequest) -> AuditResponse:
    try:
        result = await swarm_orchestrator.auditor.audit_code(request.code_snippet, request.context or "")
        return AuditResponse(
            success=True,
            is_valid=result.get("is_valid", True),
            severity=result.get("severity", "NONE"),
            issues=result.get("issues", [])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha na auditoria: {str(e)}")

@router.post(
    "/run-test",
    response_model=RunTestResponse,
    summary="Executa script em sandbox isolada via TestRunnerAgent"
)
async def run_test(request: RunTestRequest) -> RunTestResponse:
    try:
        res = await swarm_orchestrator.runner.run_code(request.script_path)
        return RunTestResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha na execução de teste: {str(e)}")

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
