"""
Test Harness - Checkout e Licenciamento Império Mutante
Testa a provisão de licença direta e a listagem de pedidos/ordens financeiras.
"""
import os
import sys
from pathlib import Path

# Garante raiz no path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from api_mutante.main import app
from api_mutante.core.security import api_key_manager

def main():
    print("--- [TEST] Checkout & Billing Orders Test Harness ---")
    client = TestClient(app)

    # 1. Obter status inicial de pedidos
    res = client.get("/v1/billing/orders")
    print(f"GET /v1/billing/orders -> Status: {res.status_code}")
    assert res.status_code == 200, f"Falha ao listar ordens: {res.text}"
    orders_initial = res.json()
    assert isinstance(orders_initial, list), "Resposta deve ser uma lista de ordens"
    initial_count = len(orders_initial)
    print(f"Total ordens iniciais: {initial_count}")

    # 2. Provisionar licença via checkout direto (PRO)
    payload_pro = {
        "customer_name": "Operador Mutante Alfa",
        "customer_email": "alfa@mutante.local",
        "tier": "PRO",
        "payment_reference": "pix_tx_998822",
        "amount_paid": 97.0
    }
    res = client.post("/v1/billing/provision-direct", json=payload_pro)
    print(f"POST /v1/billing/provision-direct (PRO) -> Status: {res.status_code}")
    assert res.status_code == 201, f"Falha ao provisionar licenca PRO: {res.text}"
    data_pro = res.json()
    assert data_pro.get("success") is True
    api_key_pro = data_pro.get("api_key")
    assert api_key_pro.startswith("mutante_pro_")
    print(f"[OK] Licença PRO gerada: {api_key_pro} | RPM: {data_pro.get('rate_limit_rpm')}")

    # 3. Provisionar licença via checkout direto (ENTERPRISE)
    payload_ent = {
        "customer_name": "Comando Central Mutante",
        "customer_email": "comando@mutante.local",
        "tier": "ENTERPRISE",
        "payment_reference": "card_ch_773311",
        "amount_paid": 497.0
    }
    res = client.post("/v1/billing/provision-direct", json=payload_ent)
    print(f"POST /v1/billing/provision-direct (ENTERPRISE) -> Status: {res.status_code}")
    assert res.status_code == 201, f"Falha ao provisionar licenca ENTERPRISE: {res.text}"
    data_ent = res.json()
    assert data_ent.get("success") is True
    api_key_ent = data_ent.get("api_key")
    assert api_key_ent.startswith("mutante_enterprise_")
    print(f"[OK] Licença ENTERPRISE gerada: {api_key_ent} | RPM: {data_ent.get('rate_limit_rpm')}")

    # 4. Verificar se ordens foram salvas e listadas
    res = client.get("/v1/billing/orders")
    assert res.status_code == 200
    orders_updated = res.json()
    assert isinstance(orders_updated, list)
    print(f"Total ordens atualizadas: {len(orders_updated)}")
    assert len(orders_updated) >= initial_count + 2, "As novas ordens não foram registradas corretamente!"
    
    # Valida formato da última ordem registrada
    latest_order = orders_updated[0]
    print(f"[OK] Última ordem auditada: {latest_order['order_id']} | Tier: {latest_order['tier']} | Cliente: {latest_order['customer_name']}")

    # 5. Validar autenticidade e rate limit das chaves geradas
    meta_pro = api_key_manager.validate_and_rate_limit(api_key_pro)
    assert meta_pro["tier"] == "PRO"
    assert meta_pro["is_active"] is True
    print(f"[OK] Chave PRO validada criptograficamente no core de segurança!")

    meta_ent = api_key_manager.validate_and_rate_limit(api_key_ent)
    assert meta_ent["tier"] == "ENTERPRISE"
    assert meta_ent["is_active"] is True
    print(f"[OK] Chave ENTERPRISE validada criptograficamente no core de segurança!")

    print("\n--- [SUCESSO] Todos os testes de Checkout & Billing passaram com 100% de integridade! ---")

if __name__ == "__main__":
    main()
