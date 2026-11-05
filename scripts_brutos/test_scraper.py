import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app

def run_scraper_validation():
    print("=" * 68)
    print("      VALIDACAO DO AGENTE AUTONOMO DE PESQUISA & SCRAPING")
    print("=" * 68)

    client = TestClient(app)

    # URL pública estável de documentação técnica para teste
    target_url = "https://example.com"
    topic = "Análise de Arquitetura de Domínios e Protocolos Web"

    print(f"[*] Disparando agente para raspar e sintetizar: {target_url}...")
    payload = {
        "url": target_url,
        "topic": topic,
        "auto_index_rag": True
    }

    res = client.post("/v1/research/scrape-and-ingest", json=payload)
    assert res.status_code == 200, f"Falha na raspagem e ingestão: {res.text}"

    data = res.json()
    assert data["success"] is True
    assert Path(data["saved_file"]).exists(), f"Arquivo não foi gerado em {data['saved_file']}!"

    print(f"\n[+] Status HTTP: 200 OK")
    print(f"[+] Título Extraído: {data['title']}")
    print(f"[+] Arquivo Gravado em 02_CONHECIMENTO: {data['filename']}")
    print(f"[+] RAG Indexação Ativada: {data['rag_indexed']}")
    print(f"\n--- [PREVIEW DO DOCUMENTO SINTETIZADO] ---")
    print(data["preview_summary"])

    print("\n" + "=" * 68)
    print("      AGENTE AUTONOMO DE PESQUISA VALIDADO COM SUCESSO!")
    print("=" * 68)

if __name__ == "__main__":
    run_scraper_validation()
