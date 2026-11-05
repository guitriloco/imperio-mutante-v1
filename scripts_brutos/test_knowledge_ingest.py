import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app

def run_ingest_test():
    print("=" * 68)
    print("    TESTE DE INGESTAO E SINTESE DE CONHECIMENTO (GEMINI)")
    print("=" * 68)

    client = TestClient(app)

    # Executa ingestão
    payload = {
        "filename": "metodo_monetizacao_v1.md",
        "model": "gemini-2.5-flash"
    }
    print(f"[*] Solicitando ingestao do documento: {payload['filename']}...")
    res = client.post("/v1/knowledge/ingest", json=payload)

    assert res.status_code == 200, f"Erro na ingestao: {res.text}"
    data = res.json()
    
    print(f"[+] Status HTTP: 200 OK")
    print(f"[+] Total processado: {data['processed_count']}")
    
    item = data["items"][0]
    print(f"[+] Arquivo fonte: {item['filename']}")
    print(f"[+] Titulo detectado: {item['title']}")
    print(f"[+] JSON estruturado salvo em: {item['data_file']}")

    # Lê o JSON gerado
    json_path = Path(item["data_file"])
    assert json_path.exists(), "Arquivo JSON estruturado não foi salvo no disco!"

    with open(json_path, "r", encoding="utf-8") as f:
        stored = json.load(f)

    print("\n" + "-" * 40 + " CONTEUDO ESTRUTURADO GERADO " + "-" * 40)
    print(f"TITULO: {stored.get('title')}")
    print(f"RESUMO: {stored.get('summary')}")
    print(f"KEY TAKEAWAYS: {stored.get('key_takeaways')}")
    print(f"ACTIONABLE INSIGHTS: {stored.get('actionable_insights')}")
    print(f"TAGS: {stored.get('tags')}")
    print("-" * 105)
    print("        SUCESSO: CONHECIMENTO DIGERIDO E INDEXADO!")
    print("=" * 68)

if __name__ == "__main__":
    run_ingest_test()
