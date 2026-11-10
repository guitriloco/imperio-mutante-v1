"""
Test Harness - Google Search Grounding, Deep Thinking & Token Telemetry
Valida a geração com busca web ao vivo, raciocínio profundo e telemetria de custos.
"""
import os
import sys
from pathlib import Path

# Garante raiz no path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from api_mutante.main import app

def main():
    print("--- [TEST] Grounding, Deep Thinking & Telemetry Test Harness ---")
    client = TestClient(app)

    # 1. Testar endpoint síncrono com Deep Thinking ativo
    payload_thinking = {
        "message": "Se eu tenho 4 caixas e em cada caixa tenho 7 maçãs, e tiro 3 no total, quantas maçãs sobram?",
        "enable_thinking": True,
        "thinking_budget": 1024
    }
    print("Enviando requisição com Deep Thinking...")
    res = client.post("/v1/chat", json=payload_thinking)
    print(f"POST /v1/chat (Thinking) -> Status: {res.status_code}")
    assert res.status_code == 200, f"Falha na requisição: {res.text}"
    data = res.json()
    assert data.get("success") is True
    assert "25" in data.get("response")
    telemetry = data.get("telemetry", {})
    print(f"[OK] Resposta obtida: {data.get('response')[:60]}...")
    print(f"[OK] Telemetria: {telemetry.get('total_tokens')} tokens totais | Pensamento: {telemetry.get('thoughts_tokens')} tokens | Latência: {telemetry.get('latency_ms')}ms")

    # 2. Testar endpoint com Google Search Grounding ativo
    payload_search = {
        "message": "Qual é a cotação do dólar hoje?",
        "enable_search": True
    }
    print("\nEnviando requisição com Google Search Grounding...")
    res = client.post("/v1/chat", json=payload_search)
    print(f"POST /v1/chat (Grounding) -> Status: {res.status_code}")
    assert res.status_code == 200, f"Falha na busca web: {res.text}"
    data_search = res.json()
    web_sources = data_search.get("web_sources", [])
    print(f"[OK] Fontes web recuperadas: {len(web_sources)}")
    for src in web_sources[:3]:
        print(f"     - {src.get('title')}: {src.get('url')[:50]}...")
    assert len(web_sources) > 0, "Deveria retornar ao menos uma fonte web quando enable_search está ativo"

    print("\n--- [SUCESSO] Bloco 1 (Backend Grounding + Thinking) 100% validado! ---")

if __name__ == "__main__":
    main()
