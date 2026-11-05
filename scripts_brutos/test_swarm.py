import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app

def run_swarm_validation():
    print("=" * 68)
    print("      VALIDACAO DO ENXAME MULTI-AGENTE & SELF-HEALING LOOP")
    print("=" * 68)

    client = TestClient(app)

    # Cria script intencionalmente quebrado para testar auto-cura
    broken_script = ROOT_DIR / "scripts_brutos" / "temp_broken_test.py"
    broken_code = """# Script com erro de tipagem e excecao intencional
def calcular_lucro_mutante():
    valores = [100, 200, "invalid_num", 400]
    total = sum(valores)
    print(f"LUCRO_TOTAL_MUTANTE: {total}")

if __name__ == "__main__":
    calcular_lucro_mutante()
"""
    broken_script.write_text(broken_code, encoding="utf-8")
    print(f"[*] Criado script com erro proposital em: {broken_script.name}")

    # Dispara auto-cura via endpoint do enxame
    print("[*] Acionando enxame SwarmOrchestrator (/v1/swarm/self-heal)...")
    payload = {
        "script_path": str(broken_script),
        "max_healing_cycles": 2
    }

    res = client.post("/v1/swarm/self-heal", json=payload)
    assert res.status_code == 200, f"Falha na auto-cura: {res.text}"

    data = res.json()
    assert data["success"] is True, "O enxame não conseguiu curar o script!"
    assert data["healing_cycles_used"] > 0, "Nenhum ciclo de cura foi aplicado!"

    print(f"\n[+] Status HTTP: 200 OK")
    print(f"[+] Sucesso da Execução Pós-Cura: {data['success']}")
    print(f"[+] Ciclos de Cura Necessários: {data['healing_cycles_used']}")
    print(f"[+] Stdout Final:\n{data['final_stdout']}")

    # Limpeza do arquivo de teste
    if broken_script.exists():
        broken_script.unlink()
        print(f"[+] Limpeza: Script temporário removido.")

    print("\n" + "=" * 68)
    print("      ENXAME MULTI-AGENTE & SELF-HEALING TOTALMENTE OPERACIONAIS!")
    print("=" * 68)

if __name__ == "__main__":
    run_swarm_validation()
