import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app

def run_rag_validation():
    print("=" * 68)
    print("      VALIDACAO DO MOTOR RAG: BUSCA SEMANTICA (EMBEDDINGS)")
    print("=" * 68)

    client = TestClient(app)

    # 1. Força a indexação e geração de embeddings
    print("[1/2] Gerando embeddings via gemini-embedding-001...")
    reindex_res = client.post("/v1/rag/reindex")
    assert reindex_res.status_code == 200, f"Falha na indexacao vetorial: {reindex_res.text}"
    reindex_data = reindex_res.json()
    print(f"      Documentos indexados com sucesso: {reindex_data.get('indexed_documents')}")

    # 2. Executa busca semântica em linguagem natural
    query = "Como criar micro-serviços lucrativos e monetizar com IA e baixo custo?"
    print(f"\n[2/2] Executando busca vetorial para a pergunta:")
    print(f"      '{query}'...")

    search_payload = {
        "query": query,
        "top_k": 2
    }
    search_res = client.post("/v1/rag/search", json=search_payload)
    assert search_res.status_code == 200, f"Falha na busca vetorial: {search_res.text}"
    
    data = search_res.json()
    print(f"\n[+] Total de correspondências encontradas: {data['total_matches']}")
    assert data["total_matches"] > 0, "Nenhum resultado retornado pelo RAG!"

    top_hit = data["results"][0]
    print(f"\n--- [TOP 1 MATCH - SCORE DE SIMILARIDADE: {top_hit['score']}] ---")
    print(f"Documento Fonte: {top_hit['source_file']}")
    print(f"Título: {top_hit['title']}")
    print(f"Resumo Semântico: {top_hit['summary']}")
    print(f"Pontos-chave: {top_hit['key_takeaways'][:2]}")
    print(f"Insights Acionáveis: {top_hit['actionable_insights'][:2]}")
    print(f"Tags: {top_hit['tags']}")

    print("\n" + "=" * 68)
    print("         RAG VETORIAL VALIDADO COM SUCESSO TOTAL!")
    print("=" * 68)

if __name__ == "__main__":
    run_rag_validation()
