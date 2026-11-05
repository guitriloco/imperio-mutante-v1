from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api_mutante.core.config import settings
from api_mutante.core.gemini_service import gemini_service
from api_mutante.rag_engine import rag_engine

router = APIRouter(prefix="/v1/chat", tags=["Conversational RAG"])

class ChatMessage(BaseModel):
    role: str = Field(..., description="Papel: 'user' ou 'model'")
    content: str = Field(..., description="Conteúdo da mensagem")

class ChatRequest(BaseModel):
    message: str = Field(..., description="Mensagem atual do usuário")
    history: List[ChatMessage] = Field(default=[], description="Histórico prévio de conversação")
    top_k: int = Field(default=2, ge=1, le=5, description="Número de documentos de contexto para recuperar")
    system_instruction: Optional[str] = Field(
        default="Você é o assistente tático do Império Mutante. Responda com precisão cirúrgica utilizando o contexto recuperado.",
        description="Diretriz de sistema"
    )

class SourceCitation(BaseModel):
    source_file: str
    title: str
    score: float

class ChatResponse(BaseModel):
    success: bool
    response: str
    sources: List[SourceCitation]
    model_used: str

@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat conversacional assíncrono com RAG e injeção de contexto"
)
async def conversational_chat(request: ChatRequest) -> ChatResponse:
    try:
        # 1. Recuperação Vetorial via RAGEngine
        rag_hits = await rag_engine.search(query=request.message, top_k=request.top_k)

        # 2. Construção do bloco de contexto
        context_blocks = []
        sources: List[SourceCitation] = []

        for hit in rag_hits:
            sources.append(SourceCitation(
                source_file=hit.get("source_file", "unknown"),
                title=hit.get("title", "Sem título"),
                score=hit.get("score", 0.0)
            ))
            def to_str(items):
                if isinstance(items, list):
                    return " ".join(str(x) for x in items)
                return str(items)

            context_blocks.append(
                f"[DOCUMENTO: {hit.get('title')}]\n"
                f"Resumo: {hit.get('summary')}\n"
                f"Pontos-chave: {to_str(hit.get('key_takeaways', []))}\n"
                f"Insights acionáveis: {to_str(hit.get('actionable_insights', []))}"
            )

        context_str = "\n\n".join(context_blocks) if context_blocks else "Nenhum documento relevante encontrado."

        # 3. Montagem do prompt contextualizado
        prompt_parts = []
        if context_str:
            prompt_parts.append(f"--- CONTEXTO RECUPERADO DA BASE DE CONHECIMENTO ---\n{context_str}\n-------------------------------------------------")

        if request.history:
            history_str = "\n".join([f"{msg.role.upper()}: {msg.content}" for msg in request.history[-6:]])
            prompt_parts.append(f"--- HISTÓRICO DA CONVERSA ---\n{history_str}\n----------------------------")

        prompt_parts.append(f"USUÁRIO: {request.message}\nRESPOSTA:")
        final_prompt = "\n\n".join(prompt_parts)

        # 4. Inferência Assíncrona no Gemini
        model_used = settings.DEFAULT_MODEL
        model_output = await gemini_service.generate_async(
            prompt=final_prompt,
            model=model_used,
            system_instruction=request.system_instruction
        )

        return ChatResponse(
            success=True,
            response=model_output,
            sources=sources,
            model_used=model_used
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na esteira de chat conversacional: {str(e)}"
        )
