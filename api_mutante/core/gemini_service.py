import asyncio
import logging
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

    async def generate_async(
        self,
        prompt: str,
        model: str | None = None,
        system_instruction: str | None = None,
        max_retries: int = 3
    ) -> str:
        """Gera conteúdo com retry exponencial resiliente contra flutuações e 503 da API."""
        primary_model = model or settings.DEFAULT_MODEL
        fallback_models = [primary_model, "gemini-2.5-flash", "gemini-2.0-flash"]
        
        # Elimina duplicatas preservando ordem
        models_to_try = list(dict.fromkeys(fallback_models))

        config = None
        if system_instruction:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction
            )

        client = self.get_client()
        last_error = None

        for target_model in models_to_try:
            for attempt in range(1, max_retries + 1):
                try:
                    response = await client.aio.models.generate_content(
                        model=target_model,
                        contents=prompt,
                        config=config
                    )
                    return response.text or ""
                except Exception as e:
                    last_error = e
                    err_msg = str(e)
                    # Se for 503 ou 429 temporário, aguarda com jitter/backoff
                    if "503" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg:
                        wait_sec = attempt * 1.5
                        logger.warning(f"Tentativa {attempt} falhou ({target_model}): {err_msg}. Aguardando {wait_sec}s...")
                        await asyncio.sleep(wait_sec)
                        continue
                    else:
                        break # Se for outro erro, tenta o próximo modelo

        raise last_error or RuntimeError("Falha em todos os modelos e retentativas.")

    async def generate_stream_async(
        self,
        prompt: str,
        model: str | None = None,
        system_instruction: str | None = None,
    ):
        """Gera streaming de tokens assíncrono via google-genai SDK."""
        target_model = model or settings.DEFAULT_MODEL
        config = None
        if system_instruction:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction
            )

        client = self.get_client()
        try:
            response_stream = await client.aio.models.generate_content_stream(
                model=target_model,
                contents=prompt,
                config=config
            )
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Erro no streaming Gemini ({target_model}): {e}")
            raise e

gemini_service = GeminiService()
