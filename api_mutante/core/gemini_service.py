from google import genai
from google.genai import types
from api_mutante.core.config import settings

class GeminiService:
    def __init__(self):
        self._client = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY não configurada no ambiente ou .env.")
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    async def generate_async(
        self,
        prompt: str,
        model: str | None = None,
        system_instruction: str | None = None
    ) -> str:
        """Gera conteúdo de forma assíncrona usando o SDK oficial google-genai."""
        target_model = model or settings.DEFAULT_MODEL
        
        config = None
        if system_instruction:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction
            )

        response = await self.client.aio.models.generate_content(
            model=target_model,
            contents=prompt,
            config=config
        )
        return response.text or ""

gemini_service = GeminiService()
