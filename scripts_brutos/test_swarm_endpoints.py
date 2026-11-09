"""
Test Harness: Validação dos Endpoints do Enxame Multi-Agente (Swarm War Room)
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app

def run_tests():
    print("=" * 65)
    print("   TESTE DE VALIDACAO - SWARM MULTI-AGENT WAR ROOM ENDPOINTS")
    print("=" * 65)
    client = TestClient(app)

    # 1. Telemetria do Enxame
    print("[1/3] Testando GET /v1/swarm/status...")
    res = client.get("/v1/swarm/status")
    assert res.status_code == 200, f"Falha status: {res.text}"
    status_data = res.json()
    assert status_data["status"] == "OPERATIONAL"
    assert "TaskPlannerAgent" in status_data["agents"]
    assert "CodeAuditorAgent" in status_data["agents"]
    print(f"      Status: OPERATIONAL | Agentes Ativos: {list(status_data['agents'].keys())}")

    # 2. Decomposição de Missão pelo TaskPlannerAgent
    print("\n[2/3] Testando POST /v1/swarm/plan...")
    plan_payload = {"task_description": "Implementar rate limiting por sliding window e persistencia em SQLite"}
    plan_res = client.post("/v1/swarm/plan", json=plan_payload)
    assert plan_res.status_code == 200, f"Falha plan: {plan_res.text}"
    plan_data = plan_res.json()
    assert plan_data["success"] is True
    assert len(plan_data["plan"]) > 0
    print(f"      Plano gerado com sucesso. {len(plan_data['plan'])} passos identificados.")
    for p in plan_data["plan"][:2]:
        print(f"      - Passo {p.get('step')}: {p.get('action')} [{p.get('target_file')}]")

    # 3. Auditoria de Código pelo CodeAuditorAgent
    print("\n[3/3] Testando POST /v1/swarm/audit...")
    bad_code = "def insecure_eval(user_input):\n    return eval(user_input)\n"
    audit_res = client.post("/v1/swarm/audit", json={"code_snippet": bad_code, "context": "Security critical"})
    assert audit_res.status_code == 200, f"Falha audit: {audit_res.text}"
    audit_data = audit_res.json()
    assert audit_data["success"] is True
    print(f"      Auditoria concluida. Valido: {audit_data['is_valid']} | Severidade: {audit_data['severity']}")
    if audit_data["issues"]:
        print(f"      Problemas detectados: {audit_data['issues']}")

    print("\n" + "=" * 65)
    print("      ENXAME MULTI-AGENTE TOTALMENTE OPERACIONAL (100% PASS)")
    print("=" * 65)
    return True

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
