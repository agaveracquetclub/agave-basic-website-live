from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import OwnerProductForm, OwnerProductImageFormSet, OwnerVariantForm, StockAdjustmentForm
from .models import InventoryAdjustment, Order, Product, StoreLocation, Variant
from .services.inventory import adjust_variant_stock
from django.utils import timezone


def owner_required(view):
    return user_passes_test(lambda user: user.is_authenticated and user.is_superuser, login_url="login")(view)


@owner_required
def dashboard(request):
    sellable_price = Coalesce("sale_price", "price", output_field=DecimalField(max_digits=12, decimal_places=2))
    inventory_value_expr = ExpressionWrapper(F("stock") * sellable_price, output_field=DecimalField(max_digits=16, decimal_places=2))
    paid_statuses = [Order.Status.PAID, Order.Status.PREPARING, Order.Status.SHIPPED, Order.Status.READY_PICKUP, Order.Status.COMPLETED]
    sales_30d = Order.objects.filter(
        status__in=paid_statuses,
        created_at__gte=timezone.now() - timedelta(days=30),
    ).aggregate(value=Coalesce(Sum("total"), Decimal("0"), output_field=DecimalField()))["value"]
    variants = Variant.objects.filter(active=True)
    context = {
        "product_count": Product.objects.filter(show_in_catalog=True).count(),
        "variant_count": variants.count(),
        "stock_units": variants.aggregate(value=Coalesce(Sum("stock"), 0))["value"],
        "inventory_value": variants.aggregate(value=Coalesce(Sum(inventory_value_expr), Decimal("0"), output_field=DecimalField()))["value"],
        "pending_orders": Order.objects.filter(status=Order.Status.PENDING_PAYMENT).count(),
        "sales_30d": sales_30d,
        "low_stock": variants.filter(stock__lte=F("low_stock_threshold")).select_related("product").order_by("stock", "product__name")[:10],
        "recent_orders": Order.objects.prefetch_related("items").order_by("-created_at")[:8],
        "recent_adjustments": InventoryAdjustment.objects.select_related("variant", "variant__product", "created_by")[:8],
        "shipping_origin": StoreLocation.objects.filter(active=True, is_shipping_origin=True).first(),
    }
    return render(request, "store/owner/dashboard.html", context)


@owner_required
def products(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    queryset = Product.objects.prefetch_related("variants", "images").annotate(
        total_stock=Coalesce(Sum("variants__stock"), 0)
    ).order_by("name")
    if query:
        queryset = queryset.filter(Q(name__icontains=query) | Q(brand__icontains=query) | Q(variants__sku__icontains=query)).distinct()
    if status == "visible":
        queryset = queryset.filter(show_in_catalog=True)
    elif status == "hidden":
        queryset = queryset.filter(show_in_catalog=False)
    return render(request, "store/owner/products.html", {"products": queryset, "query": query, "status": status})


def _product_form(request, instance=None):
    product = instance or Product()
    form = OwnerProductForm(request.POST or None, request.FILES or None, instance=product)
    images = OwnerProductImageFormSet(request.POST or None, request.FILES or None, instance=product, prefix="images")
    if request.method == "POST" and form.is_valid() and images.is_valid():
        with transaction.atomic():
            product = form.save()
            images.instance = product
            images.save()
        messages.success(request, f"{product.name} guardado.")
        return redirect("store:owner_product_edit", product.pk)
    return render(request, "store/owner/product_form.html", {"form": form, "image_formset": images, "product": instance})


@owner_required
def product_create(request):
    return _product_form(request)


@owner_required
def product_edit(request, pk):
    return _product_form(request, get_object_or_404(Product, pk=pk))


@owner_required
@require_POST
def product_archive(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.show_in_catalog = False
    product.featured = False
    product.save(update_fields=["show_in_catalog", "featured", "updated_at"])
    product.variants.update(active=False)
    messages.success(request, f"{product.name} fue archivado. No se eliminó ningún registro.")
    return redirect("store:owner_products")


@owner_required
@require_POST
def product_restore(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.show_in_catalog = True
    product.save(update_fields=["show_in_catalog", "updated_at"])
    messages.success(request, "Producto visible nuevamente. Activa individualmente las variantes que quieras vender.")
    return redirect("store:owner_products")


@owner_required
def variants(request, product_pk):
    product = get_object_or_404(Product.objects.prefetch_related("variants"), pk=product_pk)
    return render(request, "store/owner/variants.html", {"product": product})


def _variant_form(request, product, instance=None):
    variant = instance or Variant(product=product)
    form = OwnerVariantForm(request.POST or None, instance=variant)
    if request.method == "POST" and form.is_valid():
        variant = form.save(commit=False)
        variant.product = product
        variant.save()
        messages.success(request, f"Variante {variant.sku} guardada.")
        return redirect("store:owner_variants", product.pk)
    return render(request, "store/owner/variant_form.html", {"form": form, "product": product, "variant": instance})


@owner_required
def variant_create(request, product_pk):
    return _variant_form(request, get_object_or_404(Product, pk=product_pk))


@owner_required
def variant_edit(request, pk):
    variant = get_object_or_404(Variant.objects.select_related("product"), pk=pk)
    return _variant_form(request, variant.product, variant)


@owner_required
@require_POST
def variant_toggle(request, pk):
    variant = get_object_or_404(Variant.objects.select_related("product"), pk=pk)
    if not variant.active and not variant.product.show_in_catalog:
        messages.error(request, "Primero vuelve a publicar el producto.")
    else:
        variant.active = not variant.active
        variant.save(update_fields=["active", "updated_at"])
        messages.success(request, "Variante activada." if variant.active else "Variante archivada sin eliminarse.")
    return redirect("store:owner_variants", variant.product_id)


@owner_required
def stock(request):
    query = request.GET.get("q", "").strip()
    only_low = request.GET.get("low") == "1"
    variants_qs = Variant.objects.select_related("product").order_by("stock", "product__name", "sku")
    if query:
        variants_qs = variants_qs.filter(Q(product__name__icontains=query) | Q(sku__icontains=query))
    if only_low:
        variants_qs = variants_qs.filter(active=True, stock__lte=F("low_stock_threshold"))
    return render(request, "store/owner/stock.html", {"variants": variants_qs, "query": query, "only_low": only_low})


@owner_required
def stock_adjust(request, variant_pk=None):
    initial = {}
    if variant_pk:
        initial["variant"] = get_object_or_404(Variant, pk=variant_pk)
    form = StockAdjustmentForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            variant, adjustment = adjust_variant_stock(
                variant=form.cleaned_data["variant"],
                operation=form.cleaned_data["operation"],
                quantity=form.cleaned_data["quantity"],
                reason=form.cleaned_data["reason"],
                reference=form.cleaned_data["reference"],
                notes=form.cleaned_data["notes"],
                actor=request.user,
            )
        except ValidationError as exc:
            form.add_error(None, "; ".join(exc.messages))
        else:
            messages.success(request, f"Stock de {variant.sku}: {variant.stock} unidades ({adjustment.delta:+d}).")
            return redirect("store:owner_stock")
    return render(request, "store/owner/stock_adjust.html", {"form": form})


@owner_required
def orders(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    queryset = Order.objects.select_related("pickup_location", "user").prefetch_related("items", "payments")
    if query:
        queryset = queryset.filter(Q(number__icontains=query) | Q(customer_name__icontains=query) | Q(customer_email__icontains=query))
    if status:
        queryset = queryset.filter(status=status)
    return render(
        request,
        "store/owner/orders.html",
        {"orders": queryset[:200], "query": query, "status": status, "status_choices": Order.Status.choices},
    )

