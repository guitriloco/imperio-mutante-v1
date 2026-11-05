import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app

def run_chat_validation():
    print("=" * 68)
    print("      VALIDACAO DO CHAT CONVERSACIONAL COM RAG CONTEXTUAL")
    print("=" * 68)

    client = TestClient(app)

    # 1. Consulta conversacional com contexto em 02_CONHECIMENTO
    query = "Explique os pilares fundamentais do nosso método de monetização e micro-serviços."
    print(f"[*] Enviando mensagem de teste: '{query}'...")

    chat_payload = {
        "message": query,
        "history": [],
        "top_k": 2
    }

    res = client.post("/v1/chat", json=chat_payload)
    assert res.status_code == 200, f"Falha no endpoint de chat: {res.text}"

    data = res.json()
    assert data["success"] is True, "Chat retornou success=False!"
    assert len(data["sources"]) > 0, "Nenhuma fonte RAG foi injetada!"

    print(f"\n[+] Status HTTP: 200 OK")
    print(f"[+] Modelo Utilizado: {data['model_used']}")
    print(f"[+] Fontes Citadas pelo RAG ({len(data['sources'])}):")
    for s in data["sources"]:
        print(f"    - [{s['source_file']}] {s['title']} (Score: {s['score']})")

    print("\n" + "-" * 30 + " RESPOSTA GERADA PELO AGENTE " + "-" * 30)
    print(data["response"])
    print("-" * 89)
    print("         CHAT CONVERSACIONAL RAG VALIDADO COM SUCESSO!")
    print("=" * 68)

if __name__ == "__main__":
    run_chat_validation()
