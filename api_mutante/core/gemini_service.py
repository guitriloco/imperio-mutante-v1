import asyncio
import logging
import time
from typing import Optional, List, Dict, Any, AsyncGenerator
from google import genai
from google.genai import types
from google.genai.errors import APIError
from api_mutante.core.config import settings

logger = logging.getLogger("api_mutante.gemini")

class GeminiService:
    def get_client(self) -> genai.Client:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY não configurada no ambiente ou .env.")
        return genai.Client(api_key=settings.GEMINI_API_KEY)

    @property
    def client(self) -> genai.Client:
        return self.get_client()

    def _build_config(
        self,
        system_instruction: Optional[str] = None,
        enable_search: bool = False,
        enable_thinking: bool = False,
        thinking_budget: int = 1024
    ) -> types.GenerateContentConfig:
        tools = []
        if enable_search:
            tools.append(types.Tool(google_search=types.GoogleSearch()))

        thinking_config = None
        if enable_thinking:
            thinking_config = types.ThinkingConfig(thinking_budget=thinking_budget)

        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools if tools else None,
            thinking_config=thinking_config
        )

    async def generate_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        enable_search: bool = False,
        enable_thinking: bool = False,
        thinking_budget: int = 1024,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Gera conteúdo com telemetria, fallback de modelos e suporte a busca/thinking."""
        primary_model = model or settings.DEFAULT_MODEL
        fallback_models = [primary_model, "gemini-2.5-flash", "gemini-2.0-flash"]
        models_to_try = list(dict.fromkeys(fallback_models))

        config = self._build_config(
            system_instruction=system_instruction,
            enable_search=enable_search,
            enable_thinking=enable_thinking,
            thinking_budget=thinking_budget
        )

        client = self.get_client()
        last_error = None
        start_time = time.time()

        for target_model in models_to_try:
            for attempt in range(1, max_retries + 1):
                try:
                    response = await client.aio.models.generate_content(
                        model=target_model,
                        contents=prompt,
                        config=config
                    )
                    latency_ms = int((time.time() - start_time) * 1000)

                    # Extrai telemetria de tokens
                    usage = response.usage_metadata
                    prompt_tokens = usage.prompt_token_count if usage else 0
                    candidates_tokens = usage.candidates_token_count if usage else 0
                    thoughts_tokens = getattr(usage, "thoughts_token_count", 0) if usage else 0
                    total_tokens = usage.total_token_count if usage else 0

                    # Extrai fontes de busca do Grounding
                    web_sources = []
                    if response.candidates:
                        cand = response.candidates[0]
                        g_meta = getattr(cand, "grounding_metadata", None)
                        if g_meta and getattr(g_meta, "grounding_chunks", None):
                            for chunk in g_meta.grounding_chunks:
                                if getattr(chunk, "web", None):
                                    web_sources.append({
                                        "title": chunk.web.title or "Fonte Web",
                                        "url": chunk.web.uri or ""
                                    })

                    return {
                        "text": response.text or "",
                        "model_used": target_model,
                        "latency_ms": latency_ms,
                        "telemetry": {
                            "prompt_tokens": prompt_tokens,
                            "candidates_tokens": candidates_tokens,
                            "thoughts_tokens": thoughts_tokens,
                            "total_tokens": total_tokens,
                            "estimated_cost_usd": round((prompt_tokens * 0.075 + candidates_tokens * 0.30) / 1_000_000, 6)
                        },
                        "web_sources": web_sources
                    }
                except Exception as e:
                    last_error = e
                    err_msg = str(e)
                    if "503" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg:
                        wait_sec = attempt * 1.5
                        logger.warning(f"Tentativa {attempt} falhou ({target_model}): {err_msg}. Aguardando {wait_sec}s...")
                        await asyncio.sleep(wait_sec)
                        continue
                    else:
                        break

        raise last_error or RuntimeError("Falha em todos os modelos e retentativas.")

    async def generate_stream_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        enable_search: bool = False,
        enable_thinking: bool = False,
        thinking_budget: int = 1024
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Gera streaming de tokens assíncrono com suporte a SSE, busca e thinking."""
        target_model = model or settings.DEFAULT_MODEL
        config = self._build_config(
            system_instruction=system_instruction,
            enable_search=enable_search,
            enable_thinking=enable_thinking,
            thinking_budget=thinking_budget
        )

        client = self.get_client()
        start_time = time.time()
        last_usage = None
        collected_web_sources = []

        try:
            response_stream = await client.aio.models.generate_content_stream(
                model=target_model,
                contents=prompt,
                config=config
            )
            async for chunk in response_stream:
                if chunk.usage_metadata:
                    last_usage = chunk.usage_metadata

                if chunk.candidates:
                    cand = chunk.candidates[0]
                    # Extrai fontes da web se houver
                    g_meta = getattr(cand, "grounding_metadata", None)
                    if g_meta and getattr(g_meta, "grounding_chunks", None):
                        for c in g_meta.grounding_chunks:
                            if getattr(c, "web", None):
                                source_item = {
                                    "title": c.web.title or "Fonte Web",
                                    "url": c.web.uri or ""
                                }
                                if source_item not in collected_web_sources:
                                    collected_web_sources.append(source_item)

                    # Extrai partes de pensamento e texto
                    if cand.content and cand.content.parts:
                        for part in cand.content.parts:
                            is_thought = getattr(part, "thought", False)
                            if is_thought and part.text:
                                yield {"type": "thought", "content": part.text}
                            elif part.text:
                                yield {"type": "token", "content": part.text}
                elif chunk.text:
                    yield {"type": "token", "content": chunk.text}

            # Emite evento de telemetria no encerramento do stream
            latency_ms = int((time.time() - start_time) * 1000)
            prompt_tokens = last_usage.prompt_token_count if last_usage else 0
            candidates_tokens = last_usage.candidates_token_count if last_usage else 0
            thoughts_tokens = getattr(last_usage, "thoughts_token_count", 0) if last_usage else 0
            total_tokens = last_usage.total_token_count if last_usage else 0

            yield {
                "type": "telemetry",
                "latency_ms": latency_ms,
                "model_used": target_model,
                "prompt_tokens": prompt_tokens,
                "candidates_tokens": candidates_tokens,
                "thoughts_tokens": thoughts_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": round((prompt_tokens * 0.075 + candidates_tokens * 0.30) / 1_000_000, 6),
                "web_sources": collected_web_sources
            }

        except Exception as e:
            logger.error(f"Erro no streaming Gemini ({target_model}): {e}")
            raise e

gemini_service = GeminiService()
