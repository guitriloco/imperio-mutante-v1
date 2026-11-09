"""
Test Harness: Validacao de Streaming SSE em Tempo Real (POST /v1/chat/stream)
"""
import sys
import asyncio
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import httpx
from api_mutante.main import app

async def run_stream_test():
    print("=" * 65)
    print("   TESTE DE VALIDACAO - STREAMING SSE EM TEMPO REAL (/v1/chat/stream)")
    print("=" * 65)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=60.0) as client:
        payload = {
            "message": "Qual e a missao primordial do Imperio Mutante? Responda em 1 frase curta.",
            "top_k": 2,
            "system_instruction": "Responda de forma concisa e direta."
        }

        print("[1/3] Disparando requisicao SSE para /v1/chat/stream...")
        async with client.stream("POST", "/v1/chat/stream", json=payload) as response:
            assert response.status_code == 200, f"Erro status {response.status_code}"
            assert "text/event-stream" in response.headers.get("content-type", "")
            print("[2/3] Conexao SSE estabelecida com sucesso. Lendo eventos...")

            meta_received = False
            tokens = []
            done_received = False

            async for line in response.aiter_lines():
                if not line:
                    continue
                if line.startswith("event:"):
                    current_event = line.replace("event:", "").strip()
                elif line.startswith("data:"):
                    raw_data = line.replace("data:", "").strip()
                    data = json.loads(raw_data)
                    
                    if current_event == "meta":
                        meta_received = True
                        print(f"      [EVENTO META] Fontes recuperadas: {len(data.get('sources', []))} | Modelo: {data.get('model_used')}")
                    elif current_event == "token":
                        t = data.get("token", "")
                        tokens.append(t)
                        sys.stdout.write(t)
                        sys.stdout.flush()
                    elif current_event == "done":
                        done_received = True
                        print("\n      [EVENTO DONE] Streaming finalizado com status:", data.get("status"))
                    elif current_event == "error":
                        print(f"\n      [EVENTO ERROR] Erro retornado: {data.get('error')}")

            print("\n[3/3] Validando assercoes do stream...")
            assert meta_received, "Evento 'meta' nao foi recebido!"
            assert len(tokens) > 0, "Nenhum token foi recebido no stream!"
            assert done_received, "Evento 'done' nao foi recebido!"
            
            full_response = "".join(tokens)
            print(f"      Total de tokens/chunks recebidos: {len(tokens)}")
            print(f"      Comprimento do texto montado: {len(full_response)} caracteres")

    print("\n" + "=" * 65)
    print("      STREAMING SSE VALIDADO COM SUCESSO ABSOLUTO (100% PASS)")
    print("=" * 65)
    return True

if __name__ == "__main__":
    success = asyncio.run(run_stream_test())
    if not success:
        sys.exit(1)
