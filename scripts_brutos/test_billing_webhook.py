import hmac
import hashlib
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app
from api_mutante.routers.billing import WEBHOOK_SECRET

def run_billing_validation():
    print("=" * 68)
    print("      VALIDACAO DO GATEWAY DE PAGAMENTOS & WEBHOOKS")
    print("=" * 68)

    client = TestClient(app)

    # 1. Simulação de Webhook Stripe: checkout.session.completed com assinatura HMAC
    print("[1/2] Simulando Webhook Stripe (checkout.session.completed)...")
    stripe_payload = {
        "id": "evt_test_webhook_stripe_12345",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_session_xyz987",
                "customer_email": "comprador.pro@empresa.com",
                "customer_name": "Sócio Diretor Pro",
                "amount_total": 9700, # R$ 97,00
                "metadata": {
                    "tier": "PRO"
                }
            }
        }
    }
    payload_bytes = json.dumps(stripe_payload).encode("utf-8")
    signature = hmac.new(WEBHOOK_SECRET.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    headers = {
        "x-signature": signature,
        "Content-Type": "application/json"
    }

    wh_res = client.post("/v1/billing/webhook", data=payload_bytes, headers=headers)
    assert wh_res.status_code == 200, f"Falha no webhook: {wh_res.text}"
    wh_data = wh_res.json()
    assert wh_data["status"] == "success"
    assert wh_data["action"] == "license_provisioned"
    assert wh_data["tier"] == "PRO"

    issued_api_key = wh_data["api_key"]
    print(f"      Status: 200 OK -> Licença Aprovisionada Automaticamente!")
    print(f"      Order ID: {wh_data['order_id']}")
    print(f"      Tier Emitido: {wh_data['tier']}")
    print(f"      Chave Entregue ao Comprador: {issued_api_key[:25]}...")

    # 2. Teste de Aprovisionamento Direto (Mercado Pago / Checkout Manual)
    print("\n[2/2] Testando aprovisionamento direto (/v1/billing/provision-direct)...")
    direct_payload = {
        "customer_email": "vip.enterprise@corporativo.com",
        "customer_name": "Corporação Mutante VIP",
        "tier": "ENTERPRISE",
        "payment_reference": "MP_PIX_TXID_998877",
        "amount_paid": 497.00
    }
    prov_res = client.post("/v1/billing/provision-direct", json=direct_payload)
    assert prov_res.status_code == 201, f"Falha no aprovisionamento: {prov_res.text}"
    prov_data = prov_res.json()
    assert prov_data["success"] is True
    assert prov_data["tier"] == "ENTERPRISE"
    assert prov_data["rate_limit_rpm"] == 300

    print(f"      Status: 201 Created -> Licença Enterprise Ativa!")
    print(f"      Chave Enterprise: {prov_data['api_key'][:25]}...")
    print(f"      Limite Liberado: {prov_data['rate_limit_rpm']} RPM (Enterprise)")

    print("\n" + "=" * 68)
    print("      GATEWAY DE PAGAMENTOS E EMISSAO DE LICENCAS VALIDADO!")
    print("=" * 68)

if __name__ == "__main__":
    run_billing_validation()
