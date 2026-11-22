import hashlib
import hmac

import requests
from django.conf import settings
from django.core.exceptions import ValidationError

from store.models import Payment


MERCADO_PAGO_PREFERENCES_URL = "https://api.mercadopago.com/checkout/preferences"
MERCADO_PAGO_PAYMENT_URL = "https://api.mercadopago.com/v1/payments/{payment_id}"
MERCADO_PAGO_REFUND_URL = "https://api.mercadopago.com/v1/payments/{payment_id}/refunds"


def create_checkout_preference(order, webhook_url, back_urls=None):
    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        raise ValidationError("Configura MERCADOPAGO_ACCESS_TOKEN.")
    back_urls = back_urls or {
        "success": settings.MERCADOPAGO_SUCCESS_URL,
        "failure": settings.MERCADOPAGO_FAILURE_URL,
        "pending": settings.MERCADOPAGO_PENDING_URL,
    }
    if not all(back_urls.values()):
        raise ValidationError("Faltan las URL de retorno de Mercado Pago.")
    payload = {
        "external_reference": order.number,
        "items": [
            {
                "id": item.sku,
                "title": f"{item.product_name} {item.variant_name}".strip(),
                "quantity": item.quantity,
                "currency_id": "MXN",
                "unit_price": float(item.unit_price),
            }
            for item in order.items.all()
        ],
        "payer": {"name": order.customer_name, "email": order.customer_email, "phone": {"number": order.customer_phone}},
        "shipments": {"cost": float(order.shipping_amount), "mode": "not_specified"},
        "back_urls": back_urls,
        "auto_return": "approved",
        "notification_url": webhook_url,
        "statement_descriptor": "AGAVE RACQUET",
        "expires": True,
        "expiration_date_to": order.stock_expires_at.isoformat(),
    }
    response = requests.post(
        MERCADO_PAGO_PREFERENCES_URL,
        json=payload,
        headers={"Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}", "Content-Type": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    Payment.objects.create(
        order=order,
        provider=Payment.Provider.MERCADO_PAGO,
        method=Payment.Method.MERCADO_PAGO,
        status=Payment.Status.PENDING,
        external_id=str(data.get("id", "")),
        amount=order.total,
        provider_response={"preference_id": data.get("id")},
    )
    return data


def validate_webhook_signature(*, x_signature, x_request_id, data_id):
    secret = settings.MERCADOPAGO_WEBHOOK_SECRET
    if not secret or not x_signature or not x_request_id or not data_id:
        return False
    parts = dict(part.split("=", 1) for part in x_signature.split(",") if "=" in part)
    ts, received = parts.get("ts"), parts.get("v1")
    if not ts or not received:
        return False
    manifest = f"id:{str(data_id).lower()};request-id:{x_request_id};ts:{ts};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)


def fetch_payment(payment_id):
    response = requests.get(
        MERCADO_PAGO_PAYMENT_URL.format(payment_id=payment_id),
        headers={"Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def refund_payment(payment_id):
    response = requests.post(
        MERCADO_PAGO_REFUND_URL.format(payment_id=payment_id),
        headers={"Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def safe_payment_payload(data):
    card = data.get("card") or {}
    return {
        "id": data.get("id"),
        "status": data.get("status"),
        "status_detail": data.get("status_detail"),
        "payment_method_id": data.get("payment_method_id"),
        "payment_type_id": data.get("payment_type_id"),
        "transaction_amount": data.get("transaction_amount"),
        "currency_id": data.get("currency_id"),
        "date_approved": data.get("date_approved"),
        "external_reference": data.get("external_reference"),
        "card": {"last_four_digits": card.get("last_four_digits")},
    }

