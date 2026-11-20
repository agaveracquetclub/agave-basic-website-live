from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from store.models import Cart, InventoryAdjustment, Order, OrderItem, Payment, Variant


@dataclass(frozen=True)
class OrderLineRequest:
    variant_id: int
    quantity: int


def _lock_variants(lines):
    quantities = {}
    for line in lines:
        if line.quantity <= 0:
            raise ValidationError("La cantidad debe ser mayor que cero.")
        quantities[line.variant_id] = quantities.get(line.variant_id, 0) + line.quantity
    variants = {
        item.id: item
        for item in Variant.objects.select_for_update().select_related("product").filter(id__in=sorted(quantities), active=True).order_by("id")
    }
    if set(variants) != set(quantities):
        raise ValidationError("Una variante ya no está disponible.")
    for variant_id, quantity in quantities.items():
        if variants[variant_id].stock < quantity:
            raise ValidationError(f"Solo quedan {variants[variant_id].stock} unidades de {variants[variant_id]}.")
    return variants, quantities


@transaction.atomic
def create_order_with_stock_hold(*, lines, user, customer_name, customer_email, customer_phone,
                                 fulfillment, pickup_location=None, shipping_address=None,
                                 shipping_rate=None, source=Order.Source.ONLINE, notes=""):
    variants, quantities = _lock_variants(lines)
    subtotal = Decimal("0")
    shipping_rate = shipping_rate or {}
    shipping_amount = Decimal(str(shipping_rate.get("amount", "0")))
    order = Order.objects.create(
        user=user if source == Order.Source.ONLINE and getattr(user, "is_authenticated", False) else None,
        source=source,
        customer_name=customer_name,
        customer_email=customer_email or "sin-correo@agave.local",
        customer_phone=customer_phone or "",
        fulfillment=fulfillment,
        pickup_location=pickup_location,
        shipping_address=shipping_address or {},
        carrier=shipping_rate.get("carrier", ""),
        shipping_service=shipping_rate.get("service", ""),
        shipping_rate_id=shipping_rate.get("rate_id", ""),
        shipping_amount=shipping_amount,
        stock_expires_at=timezone.now() + timedelta(minutes=settings.STOCK_HOLD_MINUTES),
        notes=notes,
    )
    for variant_id, quantity in quantities.items():
        variant = variants[variant_id]
        unit_price = variant.current_price
        subtotal += unit_price * quantity
        variant.stock -= quantity
        variant.save(update_fields=["stock", "updated_at"])
        OrderItem.objects.create(
            order=order,
            variant=variant,
            sku=variant.sku,
            product_name=variant.product.name,
            variant_name=variant.name,
            attributes=variant.attributes,
            unit_price=unit_price,
            quantity=quantity,
        )
        InventoryAdjustment.objects.create(
            variant=variant,
            delta=-quantity,
            reason=InventoryAdjustment.Reason.ONLINE_SALE if source == Order.Source.ONLINE else InventoryAdjustment.Reason.EXTERNAL_SALE,
            reference=order.number,
            created_by=user if getattr(user, "is_authenticated", False) else None,
        )
    order.subtotal = subtotal
    order.total = subtotal + shipping_amount
    order.save(update_fields=["subtotal", "total", "updated_at"])
    return order


@transaction.atomic
def release_order_stock(order, *, status=Order.Status.CANCELLED, actor=None):
    order = Order.objects.select_for_update().prefetch_related("items").get(pk=order.pk)
    if order.stock_released or order.status in {Order.Status.PAID, Order.Status.PREPARING, Order.Status.SHIPPED, Order.Status.COMPLETED}:
        return order
    variants = {
        v.id: v for v in Variant.objects.select_for_update().filter(id__in=[x.variant_id for x in order.items.all() if x.variant_id]).order_by("id")
    }
    for item in order.items.all():
        if item.variant_id and item.variant_id in variants:
            variant = variants[item.variant_id]
            variant.stock += item.quantity
            variant.save(update_fields=["stock", "updated_at"])
            InventoryAdjustment.objects.create(
                variant=variant,
                delta=item.quantity,
                reason=InventoryAdjustment.Reason.CANCELLATION,
                reference=order.number,
                created_by=actor,
            )
    order.status = status
    order.stock_released = True
    order.save(update_fields=["status", "stock_released", "updated_at"])
    return order


@transaction.atomic
def approve_order_payment(order, *, payment, provider_payload=None):
    order = Order.objects.select_for_update().get(pk=order.pk)
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if order.stock_released:
        raise ValidationError("El stock de este pedido ya fue liberado; requiere revisión manual.")
    payment.status = Payment.Status.APPROVED
    payment.paid_at = timezone.now()
    if provider_payload is not None:
        payment.provider_response = provider_payload
    payment.save(update_fields=["status", "paid_at", "provider_response", "updated_at"])
    order.status = Order.Status.PAID
    order.stock_expires_at = None
    order.save(update_fields=["status", "stock_expires_at", "updated_at"])
    return order


@transaction.atomic
def create_external_sale(*, lines, staff_user, customer_name, customer_email, customer_phone, payment_method, notes=""):
    order = create_order_with_stock_hold(
        lines=lines,
        user=staff_user,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        fulfillment=Order.Fulfillment.PICKUP,
        source=Order.Source.ADMIN,
        notes=notes,
    )
    payment = Payment.objects.create(
        order=order,
        provider=Payment.Provider.MANUAL,
        method=payment_method,
        status=Payment.Status.PENDING,
        amount=order.total,
    )
    return approve_order_payment(order, payment=payment)


def cart_to_line_requests(cart: Cart):
    return [OrderLineRequest(item.variant_id, item.quantity) for item in cart.items.all()]


def release_expired_holds(*, limit=100):
    expired_ids = list(
        Order.objects.filter(
            status=Order.Status.PENDING_PAYMENT,
            stock_released=False,
            stock_expires_at__lte=timezone.now(),
        ).values_list("id", flat=True)[:limit]
    )
    for order_id in expired_ids:
        release_order_stock(Order(pk=order_id), status=Order.Status.EXPIRED)
    return len(expired_ids)


@transaction.atomic
def adjust_variant_stock(*, variant, operation, quantity, reason, actor, reference="", notes=""):
    locked = Variant.objects.select_for_update().select_related("product").get(pk=variant.pk)
    if operation == "add":
        delta = quantity
    elif operation == "remove":
        delta = -quantity
    elif operation == "set":
        delta = quantity - locked.stock
    else:
        raise ValidationError("Operación de inventario desconocida.")
    if locked.stock + delta < 0:
        raise ValidationError(f"No puedes retirar {quantity}; solo hay {locked.stock} unidades.")
    if delta == 0:
        raise ValidationError("El ajuste no cambia las existencias.")
    locked.stock += delta
    locked.save(update_fields=["stock", "updated_at"])
    adjustment = InventoryAdjustment.objects.create(
        variant=locked,
        delta=delta,
        reason=reason,
        reference=reference,
        notes=notes,
        created_by=actor,
    )
    return locked, adjustment

