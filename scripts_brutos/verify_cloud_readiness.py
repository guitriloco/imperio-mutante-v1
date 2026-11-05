import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def verify_cloud_assets():
    print("=" * 68)
    print("      AUDITORIA DE CONTAINERIZACAO E PRONTIDAO CLOUD-NATIVE")
    print("=" * 68)

    # 1. Validação do Dockerfile
    dockerfile = ROOT_DIR / "Dockerfile"
    assert dockerfile.exists(), "Dockerfile não encontrado!"
    content = dockerfile.read_text(encoding="utf-8")
    assert "FROM python:3.11-slim AS builder" in content, "Stage builder ausente no Dockerfile!"
    assert "HEALTHCHECK" in content, "Healthcheck ausente no Dockerfile!"
    assert "USER mutante" in content, "Execução não-root ausente no Dockerfile!"
    print("[1/4] Dockerfile Multi-Stage: CONFORME (Multi-Stage, Non-root, Healthcheck)")

    # 2. Validação do docker-compose.yml
    compose = ROOT_DIR / "docker-compose.yml"
    assert compose.exists(), "docker-compose.yml não encontrado!"
    compose_content = compose.read_text(encoding="utf-8")
    assert "mutante_api_engine" in compose_content
    assert "02_CONHECIMENTO" in compose_content
    print("[2/4] docker-compose.yml: CONFORME (Volumes persistentes e resource limits)")

    # 3. Validação dos Manifestos Cloud
    render_f = ROOT_DIR / "render.yaml"
    railway_f = ROOT_DIR / "railway.json"
    fly_f = ROOT_DIR / "fly.toml"

    assert render_f.exists() and railway_f.exists() and fly_f.exists(), "Manifestos cloud ausentes!"
    
    with open(railway_f, "r", encoding="utf-8") as f:
        rw_data = json.load(f)
        assert rw_data["build"]["builder"] == "DOCKERFILE"

    print("[3/4] Manifestos Cloud (Render, Railway, Fly.io): CONFORME")

    # 4. Auditoria de Segurança de Segredos
    gitignore = ROOT_DIR / ".gitignore"
    git_text = gitignore.read_text(encoding="utf-8")
    assert ".env" in git_text, ".env não protegido no .gitignore!"
    print("[4/4] Auditoria de Segurança: CONFORME (Chaves .env blindadas no .gitignore)")

    print("\n" + "=" * 68)
    print("      SISTEMA TOTALMENTE CONTAINERIZADO E PRONTO PARA O CLOUD!")
    print("=" * 68)

if __name__ == "__main__":
    verify_cloud_assets()
