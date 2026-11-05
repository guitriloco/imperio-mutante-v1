import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app

def run_dashboard_validation():
    print("=" * 68)
    print("      VALIDACAO DE INTEGRACAO: FRONTEND DASHBOARD & BACKEND")
    print("=" * 68)

    client = TestClient(app)

    # 1. Teste de montagem estática do Dashboard
    print("[1/4] Testando acesso ao Painel Web GET /dashboard/ ...")
    dash_res = client.get("/dashboard/")
    assert dash_res.status_code == 200, f"Falha ao carregar dashboard: {dash_res.status_code}"
    assert "Império Mutante - Painel de Controle Soberano" in dash_res.text
    print("      Status: 200 OK -> Interface HTML carregada com sucesso.")

    # 2. Teste da API de Prompts
    print("\n[2/4] Testando comunicacao com API de Prompts GET /v1/prompts ...")
    prompts_res = client.get("/v1/prompts")
    assert prompts_res.status_code == 200
    prompts = prompts_res.json()
    print(f"      Status: 200 OK -> {len(prompts)} template(s) carregado(s).")
    assert any(p["name"] == "knowledge_summarizer" for p in prompts)

    # 3. Teste de criacao de template (exportacao AI Studio)
    print("\n[3/4] Testando criacao de template POST /v1/prompts ...")
    new_template = {
        "name": "extrator_insights_mutante",
        "system_instruction": "Você é o especialista em monetização do Império Mutante.",
        "template": "Extraia 3 ideias lucrativas a partir de: {tema}"
    }
    create_res = client.post("/v1/prompts", json=new_template)
    assert create_res.status_code == 201
    print(f"      Status: 201 Created -> Template '{new_template['name']}' registrado.")

    # 4. Teste da API de Conhecimento
    print("\n[4/4] Testando consulta a documentos indexados GET /v1/knowledge/documents ...")
    docs_res = client.get("/v1/knowledge/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json()
    print(f"      Status: 200 OK -> {len(docs)} documento(s) indexado(s) encontrado(s).")

    print("\n" + "=" * 68)
    print("      INTEGRACAO VISUAL & BACKEND TOTALMENTE OPERACIONAL!")
    print("=" * 68)

if __name__ == "__main__":
    run_dashboard_validation()
