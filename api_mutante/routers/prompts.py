from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from api_mutante.prompts_manager import prompts_manager

router = APIRouter(prefix="/v1/prompts", tags=["Prompts"])

class TemplateDetail(BaseModel):
    name: str
    system_instruction: str
    template: str

class SaveTemplateRequest(BaseModel):
    name: str = Field(..., description="Identificador único do template")
    template: str = Field(..., description="Corpo do prompt com variáveis {var}")
    system_instruction: str = Field(default="", description="Diretriz de sistema")

@router.get(
    "",
    response_model=List[TemplateDetail],
    summary="Lista todos os templates de prompt disponíveis"
)
async def list_prompts() -> List[TemplateDetail]:
    prompts_manager.reload_from_disk()
    return [
        TemplateDetail(
            name=v["name"],
            system_instruction=v.get("system_instruction", ""),
            template=v["template"]
        )
        for v in prompts_manager._templates.values()
    ]

@router.post(
    "",
    response_model=TemplateDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra ou atualiza um template de prompt exportado do AI Studio/Stitch"
)
async def create_or_update_prompt(payload: SaveTemplateRequest) -> TemplateDetail:
    try:
        prompts_manager.save_template(
            name=payload.name,
            template=payload.template,
            system_instruction=payload.system_instruction
        )
        return TemplateDetail(
            name=payload.name,
            system_instruction=payload.system_instruction,
            template=payload.template
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao salvar template: {str(e)}"
        )
