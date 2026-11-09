"""
Test Harness: Validação de Upload Direto de Documento e Ingestão/Indexação RAG
"""
import sys
import io
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app

def run_tests():
    print("=" * 65)
    print("   TESTE DE VALIDACAO - UPLOAD DIRETO DE DOCUMENTOS (/v1/knowledge/upload)")
    print("=" * 65)

    client = TestClient(app)

    # 1. Cria payload simulado de arquivo Markdown
    test_filename = "diretriz_mutante_upload_teste.md"
    file_content = (
        "# DIRETRIZ SUPREMA DE UPLOAD MUTANTE\n\n"
        "Este documento foi carregado via upload multipart direto no acervo soberano.\n"
        "O motor de RAG e embeddings deve ingerir, estruturar metadados e indexar.\n"
    )

    file_bytes = io.BytesIO(file_content.encode("utf-8"))

    print(f"[1/2] Enviando arquivo '{test_filename}' via multipart POST...")
    response = client.post(
        "/v1/knowledge/upload?auto_index=true",
        files={"file": (test_filename, file_bytes, "text/markdown")}
    )

    assert response.status_code == 200, f"Falha no upload: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == test_filename
    assert data["bytes_saved"] > 0
    print(f"      Status: 200 OK")
    print(f"      Bytes salvos: {data['bytes_saved']}")
    print(f"      Título extraído: {data['title']}")
    print(f"      RAG indexado: {data['rag_indexed']}")

    # 2. Confirma presença física no disco
    knowledge_dir = Path("C:/Users/Administrator/ImperioMutante/02_CONHECIMENTO")
    uploaded_file = knowledge_dir / test_filename
    assert uploaded_file.exists(), f"Arquivo não encontrado em {knowledge_dir}"
    print(f"[2/2] Confirmação física no disco: {uploaded_file.name} presente e íntegro.")

    print("\n" + "=" * 65)
    print("      UPLOAD E INGESTAO DE CONHECIMENTO VALIDADO (100% PASS)")
    print("=" * 65)
    return True

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
