import asyncio
import os
import sys
from dotenv import load_dotenv
from google import genai

load_dotenv()

async def run_pipeline(prompt: str) -> str:
    """Executa consulta assíncrona ao modelo Gemini utilizando o SDK oficial."""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "sua_chave_aqui_do_google_ai_studio":
        print("[ERRO] Chave GEMINI_API_KEY nao configurada no arquivo .env.")
        print("[ACAO] Insira sua chave no arquivo .env para executar chamadas reais.")
        return ""

    # Inicializa cliente assíncrono oficial
    client = genai.Client(api_key=api_key)
    
    print(f"[*] Enviando prompt ao modelo gemini-2.5-flash...")
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

async def main():
    print("=" * 60)
    print("        IMPERIO MUTANTE - PIPELINE GEMINI ONLINE")
    print("=" * 60)
    
    prompt_teste = "Apresente o status do sistema do Império Mutante em uma frase cirurgica."
    resultado = await run_pipeline(prompt_teste)
    
    if resultado:
        print("\n[RESPOSTA GEMINI]:")
        print(resultado)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
