from django.contrib import admin, messages
from django.db import transaction
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Address,
    Cart,
    CartItem,
    CustomerProfile,
    InventoryAdjustment,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductImage,
    StoreLocation,
    Variant,
)


admin.site.site_header = "Agave Racquet Club"
admin.site.site_title = "Administración Agave"
admin.site.index_title = "Catálogo, inventario y pedidos"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    fields = ("sku", "name", "attributes", "price", "sale_price", "stock", "active")
    readonly_fields = ("stock",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category", "authenticity", "show_in_catalog", "featured", "updated_at")
    list_filter = ("category", "authenticity", "show_in_catalog", "featured")
    search_fields = ("name", "brand", "reference_model_name", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (ProductImageInline, VariantInline)
    actions = ("publish_verified", "hide_products")
    fieldsets = (
        ("Producto", {"fields": ("name", "slug", "brand", "reference_model_name", "description", "category", "sports", "specifications")} ),
        ("Publicación", {"fields": ("authenticity", "show_in_catalog", "featured", "discount_percent")} ),
        ("Empaque para Envia.com", {"fields": (
            "package_weight_kg", "package_length_cm", "package_width_cm",
            "package_height_cm", "units_per_package",
        )}),
    )

    @admin.action(description="Publicar productos seleccionados")
    def publish_verified(self, request, queryset):
        updated = queryset.update(show_in_catalog=True)
        self.message_user(request, f"{updated} productos publicados.")

    @admin.action(description="Ocultar del catálogo")
    def hide_products(self, request, queryset):
        queryset.update(show_in_catalog=False)


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "name", "price", "sale_price", "stock", "shipping_ready", "active")
    list_filter = ("active", "product__category")
    search_fields = ("sku", "product__name")
    readonly_fields = ("stock",)
    exclude = ("weight_kg", "length_cm", "width_cm", "height_cm")

    @admin.display(boolean=True, description="Envío configurado")
    def shipping_ready(self, obj):
        return obj.has_shipping_dimensions


@admin.register(InventoryAdjustment)
class InventoryAdjustmentAdmin(admin.ModelAdmin):
    list_display = ("created_at", "variant", "delta", "reason", "reference", "created_by")
    list_filter = ("reason", "created_at")
    search_fields = ("variant__sku", "variant__product__name", "reference")
    readonly_fields = ("created_at", "created_by")

    def has_change_permission(self, request, obj=None):
        return False if obj else super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if change:
            return
        with transaction.atomic():
            variant = Variant.objects.select_for_update().get(pk=obj.variant_id)
            if variant.stock + obj.delta < 0:
                raise ValueError("El ajuste dejaría inventario negativo.")
            variant.stock += obj.delta
            variant.save(update_fields=["stock", "updated_at"])
            obj.created_by = request.user
            super().save_model(request, obj, form, change)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("variant", "sku", "product_name", "variant_name", "attributes", "unit_price", "quantity", "line_total")

    @admin.display(description="Total")
    def line_total(self, obj):
        return obj.total


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("provider", "method", "status", "external_id", "amount", "currency", "card_brand", "card_last4", "paid_at", "created_at")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "customer_name", "source", "status", "fulfillment", "total", "created_at")
    list_filter = ("source", "status", "fulfillment", "created_at")
    search_fields = ("number", "customer_name", "customer_email", "tracking_number")
    readonly_fields = ("number", "user", "source", "subtotal", "shipping_amount", "total", "stock_expires_at", "stock_released", "created_at", "updated_at", "external_sale_link")
    inlines = (OrderItemInline, PaymentInline)
    actions = ("cancel_pending_orders",)
    fieldsets = (
        ("Pedido", {"fields": ("number", "source", "status", "user", "created_at", "updated_at", "external_sale_link")}),
        ("Cliente", {"fields": ("customer_name", "customer_email", "customer_phone")}),
        ("Entrega", {"fields": ("fulfillment", "pickup_location", "shipping_address", "carrier", "shipping_service", "tracking_number", "tracking_url")}),
        ("Totales", {"fields": ("subtotal", "shipping_amount", "total")}),
        ("Control de stock", {"fields": ("stock_expires_at", "stock_released")}),
        ("Notas", {"fields": ("notes",)}),
    )

    @admin.display(description="Venta externa")
    def external_sale_link(self, obj):
        return format_html('<a class="button" href="{}">Registrar nueva venta externa</a>', reverse("store:external_sale"))

    @admin.action(description="Cancelar pedidos pendientes y devolver stock")
    def cancel_pending_orders(self, request, queryset):
        from .services.inventory import release_order_stock

        allowed = queryset.filter(status=Order.Status.PENDING_PAYMENT, stock_released=False)
        count = 0
        for order in allowed:
            release_order_stock(order, status=Order.Status.CANCELLED, actor=request.user)
            count += 1
        self.message_user(request, f"{count} pedidos cancelados; el stock fue devuelto.")


@admin.register(StoreLocation)
class StoreLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_shipping_origin", "pickup_enabled", "active")
    list_filter = ("is_shipping_origin", "pickup_enabled", "active")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "provider", "method", "status", "amount", "card_display", "created_at")
    list_filter = ("provider", "method", "status")
    search_fields = ("order__number", "external_id")
    readonly_fields = ("provider_response", "created_at", "updated_at")

    @admin.display(description="Tarjeta")
    def card_display(self, obj):
        return f"{obj.card_brand} •••• {obj.card_last4}" if obj.card_last4 else "—"


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "city", "state", "postal_code", "is_default")
    search_fields = ("user__username", "recipient_name", "street", "postal_code")


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "created_at")
    search_fields = ("user__username", "user__email", "phone")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "status", "updated_at")
    list_filter = ("status",)
    readonly_fields = ("user", "session_key", "status", "created_at", "updated_at")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "variant", "quantity", "updated_at")

