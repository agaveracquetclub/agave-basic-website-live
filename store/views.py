import json
from decimal import Decimal

import requests
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import (
    AddToCartForm,
    AddressForm,
    CheckoutForm,
    ExternalSaleHeaderForm,
    ExternalSaleLineFormSet,
    RegistrationForm,
)
from .models import Address, Cart, CartItem, Order, Payment, Product, Variant
from .services.carts import get_cart
from .services.inventory import (
    OrderLineRequest,
    approve_order_payment,
    cart_to_line_requests,
    create_external_sale,
    create_order_with_stock_hold,
    release_expired_holds,
    release_order_stock,
)
from .services.payments import create_checkout_preference, fetch_payment, refund_payment, safe_payment_payload, validate_webhook_signature
from .services.shipping import ShippingConfigurationError, quote_shipping


def home(request):
    release_expired_holds(limit=25)
    products = Product.objects.filter(show_in_catalog=True, variants__active=True).distinct().prefetch_related("images", "variants")[:8]
    return render(request, "store/home.html", {"products": products})


def catalog(request):
    release_expired_holds(limit=25)
    products = Product.objects.filter(show_in_catalog=True, variants__active=True).distinct().prefetch_related("images", "variants")
    category = request.GET.get("categoria", "").strip()
    if category:
        products = products.filter(category=category)
    categories = Product.objects.filter(show_in_catalog=True).values_list("category", flat=True).distinct().order_by("category")
    return render(request, "store/catalog.html", {"products": products, "categories": categories, "selected_category": category})


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.prefetch_related("images", "variants"), slug=slug, show_in_catalog=True)
    form = AddToCartForm(product=product)
    return render(request, "store/product_detail.html", {"product": product, "form": form})


@require_POST
def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug, show_in_catalog=True)
    form = AddToCartForm(request.POST, product=product)
    if form.is_valid():
        variant = form.cleaned_data["variant_id"]
        quantity = form.cleaned_data["quantity"]
        if quantity > variant.stock:
            messages.error(request, f"Solo hay {variant.stock} unidades disponibles.")
        else:
            cart = get_cart(request)
            item, created = CartItem.objects.get_or_create(cart=cart, variant=variant, defaults={"quantity": quantity})
            if not created:
                item.quantity = min(item.quantity + quantity, variant.stock)
                item.save(update_fields=["quantity", "updated_at"])
            messages.success(request, "Producto agregado al carrito.")
            return redirect("store:cart")
    return render(request, "store/product_detail.html", {"product": product, "form": form})


def cart_view(request):
    cart = get_cart(request, create=False)
    return render(request, "store/cart.html", {"cart": cart})


@require_POST
def update_cart(request, item_id):
    cart = get_cart(request, create=False)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except ValueError:
        quantity = 1
    if quantity <= 0:
        item.delete()
    else:
        item.quantity = min(quantity, item.variant.stock)
        item.save(update_fields=["quantity", "updated_at"])
    return redirect("store:cart")


def register(request):
    if request.user.is_authenticated:
        return redirect("store:catalog")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        get_cart(request)
        messages.success(request, "Tu cuenta está lista.")
        return redirect("store:catalog")
    return render(request, "registration/register.html", {"form": form})


@login_required
def address_create(request):
    form = AddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        if address.is_default:
            request.user.addresses.update(is_default=False)
        address.save()
        messages.success(request, "Dirección guardada.")
        return redirect("store:checkout")
    return render(request, "store/address_form.html", {"form": form})


@login_required
def checkout(request):
    cart = get_cart(request, create=False)
    if not cart or not cart.items.exists():
        messages.info(request, "Tu carrito está vacío.")
        return redirect("store:catalog")
    form = CheckoutForm(request.POST or None, user=request.user)
    return render(request, "store/checkout.html", {"cart": cart, "form": form})


def _cart_signature(cart):
    return "|".join(f"{item.variant_id}:{item.quantity}:{item.updated_at.timestamp()}" for item in cart.items.order_by("variant_id"))


@login_required
@require_POST
def shipping_quotes(request):
    cart = get_cart(request, create=False)
    address = get_object_or_404(Address, pk=request.POST.get("address_id"), user=request.user)
    try:
        quotes, packing = quote_shipping(cart=cart, address=address)
    except ShippingConfigurationError as exc:
        return JsonResponse({"error": "; ".join(exc.messages)}, status=400)
    except requests.RequestException:
        return JsonResponse({"error": "No fue posible comunicarse con Envia.com. Intenta de nuevo."}, status=502)
    request.session["agave_shipping_quotes"] = {
        "cart": _cart_signature(cart),
        "address_id": address.id,
        "rates": {q["rate_id"]: q for q in quotes if q["rate_id"]},
    }
    return JsonResponse({"quotes": quotes, "packing": packing})


@login_required
@require_POST
def place_order(request):
    cart = get_cart(request, create=False)
    if not cart or not cart.items.exists():
        return redirect("store:catalog")
    form = CheckoutForm(request.POST, user=request.user)
    if not form.is_valid():
        return render(request, "store/checkout.html", {"cart": cart, "form": form})
    fulfillment = form.cleaned_data["fulfillment"]
    address = form.cleaned_data.get("address")
    pickup = form.cleaned_data.get("pickup_location")
    shipping_rate = {}
    if fulfillment == Order.Fulfillment.SHIPPING:
        rate_id = form.cleaned_data.get("shipping_rate_id")
        quote_state = request.session.get("agave_shipping_quotes", {})
        shipping_rate = quote_state.get("rates", {}).get(rate_id)
        if (
            not shipping_rate
            or quote_state.get("cart") != _cart_signature(cart)
            or quote_state.get("address_id") != address.id
        ):
            form.add_error(None, "Vuelve a cotizar y selecciona una opción de envío.")
            return render(request, "store/checkout.html", {"cart": cart, "form": form})
    try:
        order = create_order_with_stock_hold(
            lines=cart_to_line_requests(cart),
            user=request.user,
            customer_name=request.user.get_full_name() or request.user.username,
            customer_email=request.user.email,
            customer_phone=request.user.customer_profile.phone,
            fulfillment=fulfillment,
            pickup_location=pickup,
            shipping_address=address.snapshot() if address else {},
            shipping_rate=shipping_rate,
        )
        webhook_url = request.build_absolute_uri(reverse("store:mercadopago_webhook"))
        preference = create_checkout_preference(order, webhook_url)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
        return redirect("store:cart")
    except Exception:
        if "order" in locals():
            release_order_stock(order, status=Order.Status.PAYMENT_FAILED)
        messages.error(request, "No fue posible iniciar el pago. Tu inventario fue liberado.")
        return redirect("store:cart")
    cart.status = Cart.Status.CONVERTED
    cart.save(update_fields=["status", "updated_at"])
    return redirect(preference.get("init_point") or preference.get("sandbox_init_point"))


@csrf_exempt
@require_POST
def mercadopago_webhook(request):
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    data_id = str((body.get("data") or {}).get("id") or request.GET.get("data.id") or "")
    if not validate_webhook_signature(
        x_signature=request.headers.get("x-signature", ""),
        x_request_id=request.headers.get("x-request-id", ""),
        data_id=data_id,
    ):
        return JsonResponse({"ok": False}, status=401)
    if body.get("type") not in {"payment", None} or not data_id:
        return JsonResponse({"ok": True})
    data = fetch_payment(data_id)
    order = get_object_or_404(Order, number=data.get("external_reference"))
    payment = order.payments.filter(provider=Payment.Provider.MERCADO_PAGO).first()
    if not payment:
        payment = Payment.objects.create(
            order=order, provider=Payment.Provider.MERCADO_PAGO,
            method=Payment.Method.MERCADO_PAGO, amount=order.total,
        )
    payment.external_id = str(data.get("id", ""))
    payment.card_brand = data.get("payment_method_id", "")[:40]
    payment.card_last4 = str((data.get("card") or {}).get("last_four_digits") or "")[-4:]
    payment.provider_response = safe_payment_payload(data)
    payment.save(update_fields=["external_id", "card_brand", "card_last4", "provider_response", "updated_at"])
    paid_amount = Decimal(str(data.get("transaction_amount", "0")))
    currency_ok = data.get("currency_id") == "MXN"
    if data.get("status") == "approved" and (paid_amount != order.total or not currency_ok):
        refund_payment(data_id)
        payment.status = Payment.Status.REFUNDED
        payment.provider_response["agave_review"] = "amount_or_currency_mismatch"
        payment.save(update_fields=["status", "provider_response", "updated_at"])
        release_order_stock(order, status=Order.Status.PAYMENT_FAILED)
        return JsonResponse({"ok": True})
    if data.get("status") == "approved":
        order.refresh_from_db()
        if order.stock_released:
            refund_payment(data_id)
            payment.status = Payment.Status.REFUNDED
            payment.save(update_fields=["status", "updated_at"])
        else:
            approve_order_payment(order, payment=payment, provider_payload=safe_payment_payload(data))
    elif data.get("status") in {"rejected", "cancelled"}:
        payment.status = Payment.Status.REJECTED if data.get("status") == "rejected" else Payment.Status.CANCELLED
        payment.save(update_fields=["status", "updated_at"])
        release_order_stock(order, status=Order.Status.PAYMENT_FAILED)
    return JsonResponse({"ok": True})


def payment_result(request, result):
    return render(request, "store/payment_result.html", {"result": result})


@login_required
def my_orders(request):
    orders = request.user.orders.prefetch_related("items", "payments")
    return render(request, "store/my_orders.html", {"orders": orders})


@staff_member_required
def external_sale(request):
    header = ExternalSaleHeaderForm(request.POST or None)
    lines = ExternalSaleLineFormSet(request.POST or None, prefix="lines")
    if request.method == "POST" and header.is_valid() and lines.is_valid():
        requests_list = [
            OrderLineRequest(row["variant"].id, row["quantity"])
            for row in lines.cleaned_data if row and not row.get("DELETE") and row.get("variant")
        ]
        try:
            order = create_external_sale(
                lines=requests_list,
                staff_user=request.user,
                customer_name=header.cleaned_data["customer_name"],
                customer_email=header.cleaned_data["customer_email"],
                customer_phone=header.cleaned_data["customer_phone"],
                payment_method=header.cleaned_data["payment_method"],
                notes=header.cleaned_data["notes"],
            )
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            messages.success(request, f"Venta {order.number} registrada y stock descontado.")
            return redirect("admin:store_order_change", order.pk)
    return render(request, "store/external_sale.html", {"header_form": header, "line_formset": lines})

