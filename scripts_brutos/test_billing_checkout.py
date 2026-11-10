"""
Test Harness - Ciclo Completo de Checkout PIX & Faturamento Império Mutante
Testa a criação de sessão com BRCode PIX padrão Banco Central, consulta de status e liquidação bancária.
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
    print("--- [TEST] Checkout PIX Dinâmico & Billing Lifecycle Test ---")
    client = TestClient(app)

    # 1. Criar sessão de checkout PIX para Plano PRO
    payload_checkout = {
        "customer_name": "Agente Operacional Bravo",
        "customer_email": "bravo@mutante.local",
        "tier": "PRO",
        "payment_method": "pix"
    }
    res = client.post("/v1/billing/create-checkout-session", json=payload_checkout)
    print(f"POST /v1/billing/create-checkout-session -> Status: {res.status_code}")
    assert res.status_code == 201, f"Falha na criação de checkout: {res.text}"
    session_data = res.json()
    order_id = session_data.get("order_id")
    assert order_id is not None
    assert session_data.get("status") == "PENDING"
    assert session_data.get("amount") == 97.0
    pix_code = session_data.get("pix_code")
    qr_svg = session_data.get("qr_code_svg")
    assert pix_code.startswith("000201"), "Código PIX Copia-e-Cola deve seguir padrão EMV Banco Central"
    assert "<svg" in qr_svg, "QR Code deve conter imagem vetorial SVG gerada"
    print(f"[OK] Ordem PIX criada: {order_id} | Valor: R$ {session_data.get('amount')}")
    print(f"[OK] BRCode PIX verificado: {pix_code[:35]}... ({len(pix_code)} chars)")
    print(f"[OK] QR Code SVG gerado: {len(qr_svg)} bytes")

    # 2. Consultar status da ordem (deve estar PENDING)
    res = client.get(f"/v1/billing/order-status/{order_id}")
    assert res.status_code == 200
    st_data = res.json()
    assert st_data.get("status") == "PENDING"
    assert st_data.get("api_key_issued") is None
    print(f"[OK] Status verificado: PENDING (aguardando liquidação bancária)")

    # 3. Simular liquidação bancária do PIX
    res = client.post(f"/v1/billing/simulate-pix-payment/{order_id}")
    print(f"POST /v1/billing/simulate-pix-payment/{order_id} -> Status: {res.status_code}")
    assert res.status_code == 200
    sim_data = res.json()
    assert sim_data.get("success") is True
    api_key_issued = sim_data.get("api_key")
    assert api_key_issued.startswith("mutante_pro_")
    print(f"[OK] Pagamento liquidado! Chave emitida: {api_key_issued}")

    # 4. Consultar status novamente (deve estar ACTIVE com a chave)
    res = client.get(f"/v1/billing/order-status/{order_id}")
    assert res.status_code == 200
    st_data2 = res.json()
    assert st_data2.get("status") == "ACTIVE"
    assert st_data2.get("api_key_issued") == api_key_issued
    assert st_data2.get("rate_limit_rpm") == 60
    print(f"[OK] Status atualizado: ACTIVE com chave vinculada")

    # 5. Validar autenticidade criptográfica e rate limit da chave emitida
    meta = api_key_manager.validate_and_rate_limit(api_key_issued)
    assert meta["tier"] == "PRO"
    assert meta["is_active"] is True
    print(f"[OK] Chave criptograficamente ativa e autorizada para o plano PRO")

    # 6. Conferir auditoria em /v1/billing/orders
    res = client.get("/v1/billing/orders")
    assert res.status_code == 200
    orders = res.json()
    assert isinstance(orders, list)
    found_order = next((o for o in orders if o.get("order_id") == order_id), None)
    assert found_order is not None
    assert found_order.get("status") == "ACTIVE"
    print(f"[OK] Ordem auditada com sucesso na listagem de ordens financeiras")

    print("\n--- [SUCESSO] Ciclo completo de Checkout PIX & Faturamento 100% aprovado! ---")

if __name__ == "__main__":
    main()
