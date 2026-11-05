import hmac
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, status, Header
from pydantic import BaseModel, Field

from api_mutante.core.security import api_key_manager, TIER_LIMITS
from api_mutante.rag_engine import DATA_DIR

router = APIRouter(prefix="/v1/billing", tags=["Billing & Payment Webhooks"])

ORDERS_DB_FILE = DATA_DIR / "orders.json"
WEBHOOK_SECRET = os.getenv("PAYMENT_WEBHOOK_SECRET", "mutante_whsec_dev_local_secret_key_2026")

def record_order(order_data: Dict[str, Any]):
    """Registra a transação e as licenças emitidas para auditoria financeira."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    orders = []
    if ORDERS_DB_FILE.exists():
        try:
            with open(ORDERS_DB_FILE, "r", encoding="utf-8") as f:
                orders = json.load(f)
        except Exception:
            orders = []
    orders.append(order_data)
    with open(ORDERS_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)

def verify_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
    """Valida a assinatura criptográfica HMAC-SHA256 do payload do webhook."""
    if not signature_header:
        return False
    expected = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)

class ManualProvisionRequest(BaseModel):
    customer_email: str = Field(..., description="Email do cliente comprador")
    customer_name: str = Field(..., description="Nome da pessoa ou empresa")
    tier: str = Field(..., description="Plano adquirido: PRO ou ENTERPRISE")
    payment_reference: str = Field(..., description="Identificador da transação no gateway")
    amount_paid: float = Field(..., description="Valor total pago")

class ProvisionResponse(BaseModel):
    success: bool
    order_id: str
    api_key: str
    tier: str
    customer_email: str
    rate_limit_rpm: int
    message: str

@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Webhook genérico e resiliente para Stripe / Mercado Pago / Hotmart"
)
async def process_payment_webhook(request: Request, x_signature: Optional[str] = Header(None)) -> Dict[str, Any]:
    body_bytes = await request.body()

    # Validação de Assinatura se configurada
    if x_signature and not verify_signature(body_bytes, x_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura de webhook inválida ou forjada."
        )

    try:
        event = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload de webhook não é um JSON válido."
        )

    event_type = event.get("type") or event.get("action") or event.get("event")

    # Mapeamento de eventos de checkout aprovado
    if event_type in [
        "checkout.session.completed",
        "payment_intent.succeeded",
        "payment.approved",
        "PURCHASE_APPROVED"
    ]:
        data_obj = event.get("data", {}).get("object", event.get("data", {}))
        
        # Extração de dados do comprador
        customer_email = (
            data_obj.get("customer_email") or
            data_obj.get("payer", {}).get("email") or
            data_obj.get("email") or
            "cliente@mutante.local"
        )
        customer_name = (
            data_obj.get("customer_name") or
            data_obj.get("payer", {}).get("first_name") or
            customer_email.split("@")[0]
        )
        tier = (
            data_obj.get("metadata", {}).get("tier") or
            event.get("tier") or
            "PRO"
        ).upper()

        if tier not in TIER_LIMITS:
            tier = "PRO"

        # Geração da Chave de API Licenciada
        api_key, meta = api_key_manager.generate_key(
            owner_name=f"{customer_name} ({customer_email})",
            tier=tier
        )

        order_record = {
            "order_id": f"ord_{int(datetime.now().timestamp())}",
            "event_type": event_type,
            "customer_email": customer_email,
            "customer_name": customer_name,
            "tier": tier,
            "api_key_issued": api_key,
            "timestamp": datetime.now().isoformat(),
            "status": "PROVISIONED"
        }
        record_order(order_record)

        return {
            "status": "success",
            "action": "license_provisioned",
            "order_id": order_record["order_id"],
            "api_key": api_key,
            "tier": tier
        }

    return {"status": "ignored", "reason": f"Evento '{event_type}' não requer aprovisionamento."}

@router.post(
    "/provision-direct",
    response_model=ProvisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aprovisionamento direto de licença após confirmação manual ou checkout integrado"
)
async def direct_provisioning(payload: ManualProvisionRequest) -> ProvisionResponse:
    tier_upper = payload.tier.upper()
    if tier_upper not in TIER_LIMITS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tier inválido: {payload.tier}. Use PRO ou ENTERPRISE."
        )

    api_key, meta = api_key_manager.generate_key(
        owner_name=f"{payload.customer_name} ({payload.customer_email})",
        tier=tier_upper
    )

    order_id = f"ord_{int(datetime.now().timestamp())}_{payload.payment_reference}"
    order_record = {
        "order_id": order_id,
        "customer_email": payload.customer_email,
        "customer_name": payload.customer_name,
        "tier": tier_upper,
        "amount_paid": payload.amount_paid,
        "payment_ref": payload.payment_reference,
        "api_key_issued": api_key,
        "timestamp": datetime.now().isoformat(),
        "status": "ACTIVE"
    }
    record_order(order_record)

    tier_cfg = TIER_LIMITS[tier_upper]
    return ProvisionResponse(
        success=True,
        order_id=order_id,
        api_key=api_key,
        tier=tier_upper,
        customer_email=payload.customer_email,
        rate_limit_rpm=tier_cfg["rpm"],
        message=f"Licença {tier_upper} gerada com sucesso. Entregue a chave ao comprador."
    )
