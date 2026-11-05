import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app

def run_mass_ingest_validation():
    print("=" * 68)
    print("      VALIDACAO DO PIPELINE DE INGESTAO EM MASSA & ETL VETORIAL")
    print("=" * 68)

    client = TestClient(app)

    # 1. Dispara ingestão em massa concorrente
    print("[1/2] Acionando pipeline assincrono em /v1/mass-ingest/execute...")
    payload = {"force_rag_reindex": True}
    res = client.post("/v1/mass-ingest/execute", json=payload)
    assert res.status_code == 200, f"Falha na ingestao em massa: {res.text}"

    data = res.json()
    assert data["total_files_scanned"] >= 3, "Quantidade insuficiente de arquivos varridos!"
    assert data["successful_extractions"] >= 3, "Extracoes com falha!"
    assert data["vector_embeddings_generated"] >= 3, "Falha na geracao vetorial!"

    print(f"\n[+] Total de Arquivos Varridos em 02_CONHECIMENTO: {data['total_files_scanned']}")
    print(f"[+] Extrações e Sínteses com Sucesso: {data['successful_extractions']}")
    print(f"[+] Embeddings Vetoriais 3072-d Gerados/Indexados: {data['vector_embeddings_generated']}")

    # 2. Teste de Busca Semântica Cruzada no RAG pós-ingestão massiva
    test_queries = [
        "Qual é o checklist para arbitragem de tráfego com afiliados de ticket alto?",
        "Como funciona a memória de longo prazo e tool use de agentes autônomos?"
    ]

    print("\n[2/2] Validando recuperacao vetorial RAG sobre a nova base:")
    for q in test_queries:
        search_res = client.post("/v1/rag/search", json={"query": q, "top_k": 1})
        assert search_res.status_code == 200
        s_data = search_res.json()
        assert s_data["total_matches"] > 0
        top = s_data["results"][0]
        print(f"      Q: '{q[:45]}...'")
        print(f"         -> Top Match: [{top['source_file']}] {top['title']} (Score: {top['score']})")

    print("\n" + "=" * 68)
    print("      INGESTAO EM MASSA & SINCRONIZACAO VETORIAL VALIDADA COM SUCESSO!")
    print("=" * 68)

if __name__ == "__main__":
    run_mass_ingest_validation()
