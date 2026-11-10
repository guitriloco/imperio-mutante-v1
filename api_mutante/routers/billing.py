import hmac
import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Request, HTTPException, status, Header
from pydantic import BaseModel, Field
import httpx
import qrcode
import qrcode.image.svg

from api_mutante.core.security import api_key_manager, TIER_LIMITS
from api_mutante.rag_engine import DATA_DIR

router = APIRouter(prefix="/v1/billing", tags=["Billing & Payment Webhooks"])

ORDERS_DB_FILE = DATA_DIR / "orders.json"
WEBHOOK_SECRET = os.getenv("PAYMENT_WEBHOOK_SECRET", "mutante_whsec_dev_local_secret_key_2026")
MP_ACCESS_TOKEN = os.getenv("MERCADO_PAGO_ACCESS_TOKEN", "").strip()

TIER_PRICES = {
    "PRO": 97.00,
    "ENTERPRISE": 497.00
}

# ---------------------------------------------------------------------------
# Helpers de Persistência e Ordens
# ---------------------------------------------------------------------------

def load_orders() -> List[Dict[str, Any]]:
    if not ORDERS_DB_FILE.exists():
        return []
    try:
        with open(ORDERS_DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_orders(orders: List[Dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(ORDERS_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)

def record_order(order_data: Dict[str, Any]) -> None:
    orders = load_orders()
    # Se já existir ordem com o mesmo ID, atualiza
    for idx, ord_item in enumerate(orders):
        if ord_item.get("order_id") == order_data.get("order_id"):
            orders[idx] = order_data
            save_orders(orders)
            return
    orders.append(order_data)
    save_orders(orders)

def find_order(order_id: str) -> Optional[Dict[str, Any]]:
    orders = load_orders()
    for o in orders:
        if o.get("order_id") == order_id:
            return o
    return None

def update_order(order_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    orders = load_orders()
    for idx, o in enumerate(orders):
        if o.get("order_id") == order_id:
            orders[idx].update(updates)
            save_orders(orders)
            return orders[idx]
    return None

# ---------------------------------------------------------------------------
# Gerador de BRCode PIX (Padrão Banco Central do Brasil - EMVCo)
# ---------------------------------------------------------------------------

def crc16_ccitt(data: str) -> str:
    crc = 0xFFFF
    for ch in data.encode("utf-8"):
        crc ^= (ch << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"

def emv_field(id_tag: str, value: str) -> str:
    return f"{id_tag}{len(value):02d}{value}"

def generate_brcode_pix(pix_key: str, merchant_name: str, merchant_city: str, amount: float, txid: str) -> str:
    merchant_account = emv_field("00", "br.gov.bcb.pix") + emv_field("01", pix_key)
    additional_data = emv_field("05", txid[:25])
    amount_str = f"{amount:.2f}"

    payload = (
        emv_field("00", "01") +
        emv_field("26", merchant_account) +
        emv_field("52", "0000") +
        emv_field("53", "986") +
        emv_field("54", amount_str) +
        emv_field("58", "BR") +
        emv_field("59", merchant_name[:25].upper()) +
        emv_field("60", merchant_city[:15].upper()) +
        emv_field("62", additional_data) +
        "6304"
    )
    crc = crc16_ccitt(payload)
    return payload + crc

def generate_qr_svg(content: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=2,
        image_factory=qrcode.image.svg.SvgPathImage
    )
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(attrib={"class": "w-full h-full"})
    return img.to_string(encoding="unicode")

# ---------------------------------------------------------------------------
# Modelos Pydantic
# ---------------------------------------------------------------------------

class CreateCheckoutRequest(BaseModel):
    customer_name: str = Field(..., description="Nome do cliente ou empresa")
    customer_email: str = Field(..., description="Email para entrega da chave")
    tier: str = Field(..., description="Plano: PRO ou ENTERPRISE")
    payment_method: str = Field(default="pix", description="Método: 'pix' ou 'card'")

class CheckoutSessionResponse(BaseModel):
    order_id: str
    status: str
    tier: str
    amount: float
    payment_method: str
    pix_code: Optional[str] = None
    qr_code_svg: Optional[str] = None
    is_sandbox: bool
    expires_at: str
    message: str

class OrderStatusResponse(BaseModel):
    order_id: str
    status: str
    tier: str
    amount_paid: Optional[float] = None
    customer_email: str
    customer_name: str
    api_key_issued: Optional[str] = None
    rate_limit_rpm: Optional[int] = None
    timestamp: str

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

# ---------------------------------------------------------------------------
# Endpoints de Checkout & Faturamento
# ---------------------------------------------------------------------------

@router.post(
    "/create-checkout-session",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inicia sessão de checkout com PIX Dinâmico ou Cartão"
)
async def create_checkout_session(payload: CreateCheckoutRequest) -> CheckoutSessionResponse:
    tier_upper = payload.tier.upper()
    if tier_upper not in TIER_LIMITS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plano inválido: {payload.tier}. Escolha PRO ou ENTERPRISE."
        )

    amount = TIER_PRICES.get(tier_upper, 97.00)
    tx_stamp = int(datetime.now().timestamp())
    order_id = f"ord_{payload.payment_method.lower()}_{tx_stamp}_{secrets.token_hex(3)}"
    expires_dt = datetime.now() + timedelta(minutes=30)
    expires_at_iso = expires_dt.isoformat()

    pix_code = None
    qr_code_svg = None
    is_sandbox = True

    if payload.payment_method.lower() == "pix":
        # Tentativa de criar PIX Oficial Mercado Pago se token presente
        if MP_ACCESS_TOKEN:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    mp_headers = {
                        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
                        "Content-Type": "application/json",
                        "X-Idempotency-Key": order_id
                    }
                    mp_body = {
                        "transaction_amount": amount,
                        "description": f"Licença Império Mutante - Plano {tier_upper}",
                        "payment_method_id": "pix",
                        "payer": {
                            "email": payload.customer_email,
                            "first_name": payload.customer_name
                        },
                        "external_reference": order_id
                    }
                    res = await client.post("https://api.mercadopago.com/v1/payments", json=mp_body, headers=mp_headers)
                    if res.status_code in [200, 201]:
                        mp_data = res.json()
                        tx_data = mp_data.get("point_of_interaction", {}).get("transaction_data", {})
                        pix_code = tx_data.get("qr_code")
                        qr_code_svg = generate_qr_svg(pix_code) if pix_code else None
                        is_sandbox = False
            except Exception:
                # Fallback seguro para gerador nativo
                pass

        # Se não há token do MP ou houve falha, usa gerador padrão BCB autêntico
        if not pix_code:
            pix_key = os.getenv("PIX_KEY", "pagamentos@imperiomutante.com.br")
            pix_code = generate_brcode_pix(
                pix_key=pix_key,
                merchant_name="IMPERIO MUTANTE",
                merchant_city="SAO PAULO",
                amount=amount,
                txid=f"MUT{tx_stamp}"
            )
            qr_code_svg = generate_qr_svg(pix_code)
            is_sandbox = True
    else:
        # Cartão de crédito / Link de pagamento
        is_sandbox = True

    # Registra ordem pendente para auditoria
    order_record = {
        "order_id": order_id,
        "customer_email": payload.customer_email,
        "customer_name": payload.customer_name,
        "tier": tier_upper,
        "amount_paid": amount,
        "payment_method": payload.payment_method.lower(),
        "pix_code": pix_code,
        "api_key_issued": None,
        "timestamp": datetime.now().isoformat(),
        "expires_at": expires_at_iso,
        "status": "PENDING"
    }
    record_order(order_record)

    return CheckoutSessionResponse(
        order_id=order_id,
        status="PENDING",
        tier=tier_upper,
        amount=amount,
        payment_method=payload.payment_method.lower(),
        pix_code=pix_code,
        qr_code_svg=qr_code_svg,
        is_sandbox=is_sandbox,
        expires_at=expires_at_iso,
        message=f"Ordem de pagamento PIX criada. Aguardando compensação bancária."
    )


@router.get(
    "/order-status/{order_id}",
    response_model=OrderStatusResponse,
    summary="Consulta o status em tempo real de uma ordem de checkout"
)
async def get_order_status(order_id: str) -> OrderStatusResponse:
    order = find_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ordem '{order_id}' não localizada."
        )

    # Se estiver pendente e Mercado Pago estiver ativo, verifica o status externo
    if order.get("status") == "PENDING" and MP_ACCESS_TOKEN and not order.get("is_sandbox", False):
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(
                    f"https://api.mercadopago.com/v1/payments/search?external_reference={order_id}",
                    headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
                )
                if res.status_code == 200:
                    results = res.json().get("results", [])
                    if results and results[0].get("status") == "approved":
                        # Aprova e emite chave
                        api_key, _ = api_key_manager.generate_key(
                            owner_name=f"{order['customer_name']} ({order['customer_email']})",
                            tier=order["tier"]
                        )
                        order = update_order(order_id, {
                            "status": "ACTIVE",
                            "api_key_issued": api_key,
                            "approved_at": datetime.now().isoformat()
                        })
        except Exception:
            pass

    tier_cfg = TIER_LIMITS.get(order["tier"], {})
    return OrderStatusResponse(
        order_id=order["order_id"],
        status=order["status"],
        tier=order["tier"],
        amount_paid=order.get("amount_paid"),
        customer_email=order["customer_email"],
        customer_name=order["customer_name"],
        api_key_issued=order.get("api_key_issued"),
        rate_limit_rpm=tier_cfg.get("rpm", 60) if order.get("api_key_issued") else None,
        timestamp=order["timestamp"]
    )


@router.post(
    "/simulate-pix-payment/{order_id}",
    response_model=ProvisionResponse,
    summary="Simula aprovação de pagamento bancário PIX para testes em ambiente de homologação"
)
async def simulate_pix_payment(order_id: str) -> ProvisionResponse:
    order = find_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ordem '{order_id}' não encontrada."
        )

    if order.get("status") == "ACTIVE" and order.get("api_key_issued"):
        tier_cfg = TIER_LIMITS[order["tier"]]
        return ProvisionResponse(
            success=True,
            order_id=order["order_id"],
            api_key=order["api_key_issued"],
            tier=order["tier"],
            customer_email=order["customer_email"],
            rate_limit_rpm=tier_cfg["rpm"],
            message="Ordem já aprovada anteriormente."
        )

    # Gera chave de API licenciada
    api_key, _ = api_key_manager.generate_key(
        owner_name=f"{order['customer_name']} ({order['customer_email']})",
        tier=order["tier"]
    )

    order = update_order(order_id, {
        "status": "ACTIVE",
        "api_key_issued": api_key,
        "simulated": True,
        "approved_at": datetime.now().isoformat()
    })

    tier_cfg = TIER_LIMITS[order["tier"]]
    return ProvisionResponse(
        success=True,
        order_id=order_id,
        api_key=api_key,
        tier=order["tier"],
        customer_email=order["customer_email"],
        rate_limit_rpm=tier_cfg["rpm"],
        message=f"Pagamento PIX confirmado com sucesso! Licença {order['tier']} ativada instantaneamente."
    )


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


@router.get(
    "/orders",
    summary="Lista todas as ordens financeiras e licenças emitidas para auditoria"
)
async def list_orders() -> List[Dict[str, Any]]:
    orders = load_orders()
    return orders[::-1]  # Retorna as mais recentes primeiro


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Webhook genérico e resiliente para Stripe / Mercado Pago / Hotmart"
)
async def process_payment_webhook(request: Request, x_signature: Optional[str] = Header(None)) -> Dict[str, Any]:
    body_bytes = await request.body()

    if x_signature:
        expected = hmac.new(WEBHOOK_SECRET.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, x_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Assinatura de webhook inválida."
            )

    try:
        event = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload inválido.")

    event_type = event.get("type") or event.get("action") or event.get("event")

    if event_type in ["checkout.session.completed", "payment_intent.succeeded", "payment.approved", "PURCHASE_APPROVED"]:
        data_obj = event.get("data", {}).get("object", event.get("data", {}))
        customer_email = data_obj.get("customer_email") or data_obj.get("email") or "cliente@mutante.local"
        customer_name = data_obj.get("customer_name") or customer_email.split("@")[0]
        tier = (data_obj.get("metadata", {}).get("tier") or event.get("tier") or "PRO").upper()
        if tier not in TIER_LIMITS:
            tier = "PRO"

        api_key, _ = api_key_manager.generate_key(
            owner_name=f"{customer_name} ({customer_email})",
            tier=tier
        )

        order_record = {
            "order_id": f"ord_wh_{int(datetime.now().timestamp())}",
            "customer_email": customer_email,
            "customer_name": customer_name,
            "tier": tier,
            "amount_paid": TIER_PRICES.get(tier, 97.0),
            "api_key_issued": api_key,
            "timestamp": datetime.now().isoformat(),
            "status": "ACTIVE"
        }
        record_order(order_record)

        return {
            "status": "success",
            "action": "license_provisioned",
            "order_id": order_record["order_id"],
            "api_key": api_key,
            "tier": tier
        }

    return {"status": "ignored", "reason": f"Evento '{event_type}' não requer ação."}
