import json
import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
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
    enable_search: bool = Field(default=False, description="Ativa Google Search Grounding para busca ao vivo na web")
    enable_thinking: bool = Field(default=False, description="Ativa modo de raciocínio profundo (Deep Thinking)")
    thinking_budget: int = Field(default=1024, description="Cota de tokens para o raciocínio")
    model: Optional[str] = Field(default=None, description="Modelo alvo: gemini-2.5-flash ou gemini-2.0-pro")

class SourceCitation(BaseModel):
    source_file: str
    title: str
    score: float

class WebSource(BaseModel):
    title: str
    url: str

class TelemetryData(BaseModel):
    prompt_tokens: int = 0
    candidates_tokens: int = 0
    thoughts_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0

class ChatResponse(BaseModel):
    success: bool
    response: str
    sources: List[SourceCitation]
    web_sources: List[WebSource] = []
    telemetry: Optional[TelemetryData] = None
    model_used: str

@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat conversacional assíncrono com RAG, Grounding e Telemetria"
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

        # 4. Inferência Assíncrona no Gemini com Search & Thinking
        model_target = request.model or settings.DEFAULT_MODEL
        gen_result = await gemini_service.generate_async(
            prompt=final_prompt,
            model=model_target,
            system_instruction=request.system_instruction,
            enable_search=request.enable_search,
            enable_thinking=request.enable_thinking,
            thinking_budget=request.thinking_budget
        )

        telemetry_raw = gen_result.get("telemetry", {})
        web_sources = [WebSource(**w) for w in gen_result.get("web_sources", [])]

        return ChatResponse(
            success=True,
            response=gen_result.get("text", ""),
            sources=sources,
            web_sources=web_sources,
            telemetry=TelemetryData(
                prompt_tokens=telemetry_raw.get("prompt_tokens", 0),
                candidates_tokens=telemetry_raw.get("candidates_tokens", 0),
                thoughts_tokens=telemetry_raw.get("thoughts_tokens", 0),
                total_tokens=telemetry_raw.get("total_tokens", 0),
                estimated_cost_usd=telemetry_raw.get("estimated_cost_usd", 0.0),
                latency_ms=gen_result.get("latency_ms", 0)
            ),
            model_used=gen_result.get("model_used", model_target)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na esteira de chat conversacional: {str(e)}"
        )


@router.post(
    "/stream",
    summary="Chat conversacional com streaming SSE em tempo real, Grounding e Telemetria"
)
async def conversational_chat_stream(request: ChatRequest):
    """Endpoint SSE para transmissão em tempo real token a token com thinking e web search."""
    async def sse_event_generator():
        try:
            # 1. Recuperação Vetorial via RAGEngine
            rag_hits = await rag_engine.search(query=request.message, top_k=request.top_k)

            # 2. Construção do bloco de contexto e fontes locais
            context_blocks = []
            sources_data = []

            for hit in rag_hits:
                sources_data.append({
                    "source_file": hit.get("source_file", "unknown"),
                    "title": hit.get("title", "Sem título"),
                    "score": hit.get("score", 0.0)
                })
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

            # 3. Emite evento inicial de metadados com as fontes locais
            model_target = request.model or settings.DEFAULT_MODEL
            meta_payload = {
                "sources": sources_data,
                "model_used": model_target,
                "enable_search": request.enable_search,
                "enable_thinking": request.enable_thinking
            }
            yield f"event: meta\ndata: {json.dumps(meta_payload)}\n\n"

            # 4. Montagem do prompt contextualizado
            prompt_parts = []
            if context_str:
                prompt_parts.append(f"--- CONTEXTO RECUPERADO DA BASE DE CONHECIMENTO ---\n{context_str}\n-------------------------------------------------")

            if request.history:
                history_str = "\n".join([f"{msg.role.upper()}: {msg.content}" for msg in request.history[-6:]])
                prompt_parts.append(f"--- HISTÓRICO DA CONVERSA ---\n{history_str}\n----------------------------")

            prompt_parts.append(f"USUÁRIO: {request.message}\nRESPOSTA:")
            final_prompt = "\n\n".join(prompt_parts)

            # 5. Transmissão contínua com discriminação de thought, token e telemetry
            async for chunk in gemini_service.generate_stream_async(
                prompt=final_prompt,
                model=model_target,
                system_instruction=request.system_instruction,
                enable_search=request.enable_search,
                enable_thinking=request.enable_thinking,
                thinking_budget=request.thinking_budget
            ):
                chunk_type = chunk.get("type")
                if chunk_type == "thought":
                    yield f"event: thought\ndata: {json.dumps({'thought': chunk.get('content', '')})}\n\n"
                elif chunk_type == "token":
                    yield f"event: token\ndata: {json.dumps({'token': chunk.get('content', '')})}\n\n"
                elif chunk_type == "telemetry":
                    yield f"event: telemetry\ndata: {json.dumps(chunk)}\n\n"

            # 6. Evento de conclusão
            yield f"event: done\ndata: {json.dumps({'status': 'completed'})}\n\n"

        except Exception as e:
            error_payload = {"error": str(e)}
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
