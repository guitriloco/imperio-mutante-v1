import sys
from pathlib import Path

# Adiciona raiz do projeto ao path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app

def run_tests():
    print("=" * 65)
    print("      TESTE DE VALIDACAO - MOTOR DE API IMPERIO MUTANTE")
    print("=" * 65)
    
    client = TestClient(app)
    
    # 1. Teste Root / Health
    print("[1/2] Testando endpoint de integridade GET / ...")
    health_res = client.get("/")
    assert health_res.status_code == 200, f"Falha no health check: {health_res.text}"
    print(f"      Status: 200 OK -> {health_res.json()}")
    
    # 2. Teste /v1/generate
    print("\n[2/2] Testando endpoint assincrono POST /v1/generate ...")
    payload = {
        "prompt": "Forneca uma confirmacao tatica de que a API do Imperio Mutante esta operacional em 1 frase.",
        "model": "gemini-2.5-flash",
        "system_instruction": "Voce e o assistente de alta precisao do Imperio Mutante."
    }
    
    gen_res = client.post("/v1/generate", json=payload)
    assert gen_res.status_code == 200, f"Falha no endpoint generate: {gen_res.text}"
    
    data = gen_res.json()
    print(f"      Status: 200 OK")
    print(f"      Modelo Utilizado: {data['model_used']}")
    print(f"      Sucesso: {data['success']}")
    print(f"\n[RESPOSTA RETORNADA PELA API]:\n{data['content']}")
    print("=" * 65)
    print("         VALIDACAO CONCLUIDA COM SUCESSO ABSOLUTO")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
