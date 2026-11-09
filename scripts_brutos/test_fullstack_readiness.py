"""
Test Harness: Validacao de Prontidao da Arquitetura Fullstack Unificada (Imperio Mutante)
"""
import sys
import os
from pathlib import Path

def test_fullstack_readiness():
    root = Path(__file__).resolve().parent.parent
    frontend_dir = root / "frontend"
    docker_compose = root / "docker-compose.yml"
    start_bat = root / "start_mutante.bat"

    print("=" * 60)
    print("VERIFICACAO DE PRONTIDAO FULLSTACK UNIFICADA")
    print("=" * 60)

    # 1. Frontend Structure
    assert frontend_dir.exists(), "Diretorio 'frontend' nao encontrado!"
    assert (frontend_dir / "package.json").exists(), "frontend/package.json ausente!"
    assert (frontend_dir / "src" / "app" / "page.tsx").exists(), "frontend/src/app/page.tsx ausente!"
    assert (frontend_dir / "Dockerfile").exists(), "frontend/Dockerfile ausente!"
    print("[OK] [FRONTEND] Estrutura Next.js App Router e Dockerfile validados.")

    # 2. Docker Compose
    assert docker_compose.exists(), "docker-compose.yml ausente!"
    compose_content = docker_compose.read_text(encoding="utf-8")
    assert "mutante-core-api:" in compose_content, "Servico API ausente no docker-compose!"
    assert "mutante-frontend-ui:" in compose_content, "Servico Frontend ausente no docker-compose!"
    assert ":3000" in compose_content, "Mapeamento de porta 3000 ausente!"
    assert ":8000" in compose_content, "Mapeamento de porta 8000 ausente!"
    print("[OK] [DOCKER] docker-compose.yml validado com orquestracao dual (API :8000 + Frontend :3000).")

    # 3. Start Script
    assert start_bat.exists(), "start_mutante.bat ausente!"
    print("[OK] [LAUNCHER] Script de 1 clique 'start_mutante.bat' validado.")

    # 4. Backend Health check & module import
    sys.path.insert(0, str(root))
    from api_mutante.main import app
    assert app is not None, "Falha ao instanciar FastAPI app!"
    print("[OK] [BACKEND] Instancia FastAPI 'api_mutante.main:app' carregada com sucesso.")

    print("\n[SUCESSO] TODOS OS CRITERIOS DE PRONTIDAO FULLSTACK FORAM ATENDIDOS!")
    return True

if __name__ == "__main__":
    success = test_fullstack_readiness()
    if not success:
        sys.exit(1)
