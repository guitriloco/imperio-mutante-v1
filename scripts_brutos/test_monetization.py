import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app

def run_monetization_validation():
    print("=" * 68)
    print("      VALIDACAO DO SUBSISTEMA DE MONETIZACAO & API KEYS")
    print("=" * 68)

    client = TestClient(app)

    # 1. Lista Tiers disponíveis
    print("[1/4] Consultando planos de monetizacao em /v1/monetization/tiers...")
    tiers_res = client.get("/v1/monetization/tiers")
    assert tiers_res.status_code == 200
    tiers_data = tiers_res.json()
    assert "FREE" in tiers_data and "PRO" in tiers_data and "ENTERPRISE" in tiers_data
    print(f"      Tiers Ativos: {list(tiers_data.keys())}")

    # 2. Emissão de Chave de API para cliente
    print("\n[2/4] Gerando Chave de API de Teste (Tier FREE - 5 RPM)...")
    key_payload = {
        "owner_name": "Empresa Cliente Alpha Ltda",
        "tier": "FREE"
    }
    gen_res = client.post("/v1/monetization/keys/generate", json=key_payload)
    assert gen_res.status_code == 201, f"Falha na geração de chave: {gen_res.text}"
    gen_data = gen_res.json()
    api_key = gen_data["api_key"]
    print(f"      Chave Emitida com Sucesso: {api_key[:20]}... [Owner: {gen_data['owner']}]")

    # 3. Teste de Autenticação Válida com a chave
    print("\n[3/4] Testando requisição com a chave de API gerada...")
    headers = {"X-API-Key": api_key}
    req_payload = {
        "prompt": "Confirmação de autenticação monetizada.",
        "model": "gemini-2.5-flash"
    }
    auth_res = client.post("/v1/generate", json=req_payload, headers=headers)
    assert auth_res.status_code == 200, f"Falha na autenticação da chave: {auth_res.text}"
    print("      Status: 200 OK -> Chave autenticada e cota contabilizada.")

    # 4. Teste de Exaustão de Rate-Limiting (Free Tier = 5 RPM)
    print("\n[4/4] Testando disparo de Rate-Limiter (limite de 5 req/min no plano FREE)...")
    rate_limit_triggered = False
    for i in range(6):
        r = client.post("/v1/generate", json=req_payload, headers=headers)
        if r.status_code == 429:
            rate_limit_triggered = True
            print(f"      [Disparo {i+1}] HTTP 429 Too Many Requests -> {r.json()['detail']}")
            break

    assert rate_limit_triggered, "O Rate-Limiter deveria ter disparado HTTP 429 após 5 requisições rápidas!"

    print("\n" + "=" * 68)
    print("      SUBSISTEMA DE MONETIZACAO & SEGURANCA VALIDADO COM SUCESSO!")
    print("=" * 68)

if __name__ == "__main__":
    run_monetization_validation()
