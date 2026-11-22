import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CustomerProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    phone = models.CharField("teléfono", max_length=20, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Address(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField("nombre", max_length=40, default="Casa")
    recipient_name = models.CharField("destinatario", max_length=160)
    phone = models.CharField("teléfono", max_length=20)
    street = models.CharField("calle", max_length=180)
    exterior_number = models.CharField("número exterior", max_length=30)
    interior_number = models.CharField("número interior", max_length=30, blank=True)
    neighborhood = models.CharField("colonia", max_length=120)
    city = models.CharField("ciudad", max_length=120)
    state = models.CharField("estado", max_length=80)
    postal_code = models.CharField("código postal", max_length=10)
    country_code = models.CharField("país", max_length=2, default="MX")
    references = models.TextField("referencias", blank=True)
    is_default = models.BooleanField("predeterminada", default=False)

    class Meta:
        verbose_name = "dirección"
        verbose_name_plural = "direcciones"
        ordering = ["-is_default", "-updated_at"]

    def __str__(self):
        return f"{self.label}: {self.street} {self.exterior_number}, {self.city}"

    def snapshot(self):
        return {
            "recipient_name": self.recipient_name,
            "phone": self.phone,
            "street": self.street,
            "exterior_number": self.exterior_number,
            "interior_number": self.interior_number,
            "neighborhood": self.neighborhood,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country_code": self.country_code,
            "references": self.references,
        }


class StoreLocation(TimeStampedModel):
    name = models.CharField("nombre", max_length=120)
    street_address = models.CharField("dirección", max_length=220)
    neighborhood = models.CharField("colonia", max_length=120, blank=True)
    city = models.CharField("ciudad", max_length=120)
    state = models.CharField("estado", max_length=80)
    postal_code = models.CharField("código postal", max_length=10)
    country_code = models.CharField("país", max_length=2, default="MX")
    contact_name = models.CharField("contacto", max_length=120, blank=True)
    contact_email = models.EmailField("correo de contacto", blank=True)
    phone = models.CharField("teléfono", max_length=20, blank=True)
    opening_hours = models.CharField("horario", max_length=180, blank=True)
    is_shipping_origin = models.BooleanField("origen de envíos", default=False)
    pickup_enabled = models.BooleanField("punto de recolección", default=False)
    active = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "sucursal o punto de entrega"
        verbose_name_plural = "sucursales y puntos de entrega"
        constraints = [
            models.UniqueConstraint(
                fields=["is_shipping_origin"],
                condition=Q(is_shipping_origin=True),
                name="one_shipping_origin",
            )
        ]

    def __str__(self):
        return f"{self.name} — {self.full_address}"

    @property
    def full_address(self):
        locality = ", ".join(part for part in [self.neighborhood, self.city, self.state] if part)
        postal = f"C.P. {self.postal_code}" if self.postal_code else ""
        country = "México" if self.country_code == "MX" else self.country_code
        return ", ".join(part for part in [self.street_address, locality, postal, country] if part)

    def envia_address(self):
        return {
            "name": self.contact_name or self.name,
            "company": "Agave Racquet Club",
            "street": self.street_address,
            "district": self.neighborhood,
            "city": self.city,
            "state": self.state,
            "postalCode": self.postal_code,
            "country": self.country_code,
            "phone": self.phone,
            "email": self.contact_email,
        }


class Product(TimeStampedModel):
    class Authenticity(models.TextChoices):
        GENERIC = "generic", "Genérico"
        VERIFIED = "verified", "Original verificado"
        UNVERIFIED = "unverified", "Sin verificar"

    name = models.CharField("nombre", max_length=180)
    slug = models.SlugField(unique=True, max_length=200)
    brand = models.CharField("marca", max_length=100, default="Agave / Genérica")
    description = models.TextField("descripción", blank=True)
    category = models.CharField("categoría", max_length=100)
    sports = models.JSONField("deportes", default=list, blank=True)
    specifications = models.JSONField("especificaciones", default=dict, blank=True)
    authenticity = models.CharField(
        "autenticidad", max_length=20, choices=Authenticity.choices, default=Authenticity.GENERIC
    )
    show_in_catalog = models.BooleanField("visible en catálogo", default=False)
    featured = models.BooleanField("destacado", default=False)
    package_weight_kg = models.DecimalField(
        "peso de envío por unidad (kg)", max_digits=8, decimal_places=3,
        null=True, blank=True, validators=[MinValueValidator(Decimal("0.001"))],
        help_text="Peso real de una unidad ya protegida para envío.",
    )
    package_length_cm = models.DecimalField(
        "largo de la caja (cm)", max_digits=8, decimal_places=2,
        null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))],
    )
    package_width_cm = models.DecimalField(
        "ancho de la caja (cm)", max_digits=8, decimal_places=2,
        null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))],
    )
    package_height_cm = models.DecimalField(
        "alto de la caja (cm)", max_digits=8, decimal_places=2,
        null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))],
    )
    units_per_package = models.PositiveSmallIntegerField(
        "unidades máximas por caja", default=1,
        validators=[MinValueValidator(1)],
        help_text="Ejemplo: una caja de raquetas que admite dos unidades usa el valor 2.",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "producto"
        verbose_name_plural = "productos"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("store:product_detail", kwargs={"slug": self.slug})

    @property
    def primary_image_url(self):
        image = self.images.order_by("position", "id").first()
        return image.url if image else ""

    @property
    def price_from(self):
        prices = [v.current_price for v in self.variants.filter(active=True)]
        return min(prices) if prices else None

    @property
    def has_shipping_dimensions(self):
        return all([
            self.package_weight_kg,
            self.package_length_cm,
            self.package_width_cm,
            self.package_height_cm,
            self.units_per_package,
        ])

    @property
    def volumetric_weight_kg(self):
        if not self.has_shipping_dimensions:
            return None
        return (
            self.package_length_cm * self.package_width_cm * self.package_height_cm
            / Decimal("5000")
        ).quantize(Decimal("0.001"))


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("archivo", upload_to="products/%Y/%m/", blank=True)
    external_url = models.CharField("URL o ruta pública", max_length=600, blank=True)
    alt_text = models.CharField("texto alternativo", max_length=180, blank=True)
    position = models.PositiveSmallIntegerField("posición", default=0)

    class Meta:
        ordering = ["position", "id"]
        verbose_name = "imagen del producto"
        verbose_name_plural = "imágenes del producto"

    @property
    def url(self):
        if self.image:
            return self.image.url
        return self.external_url

    def clean(self):
        if not self.image and not self.external_url:
            raise ValidationError("Agrega un archivo o una URL externa.")


class Variant(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField("nombre de variante", max_length=120, blank=True)
    attributes = models.JSONField("opciones", default=dict, blank=True)
    price = models.DecimalField("precio", max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    sale_price = models.DecimalField(
        "precio de oferta", max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0"))]
    )
    stock = models.PositiveIntegerField("existencias", default=0)
    low_stock_threshold = models.PositiveIntegerField("alerta de stock", default=2)
    weight_kg = models.DecimalField("peso (kg)", max_digits=8, decimal_places=3, null=True, blank=True, validators=[MinValueValidator(Decimal("0.001"))])
    length_cm = models.DecimalField("largo (cm)", max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    width_cm = models.DecimalField("ancho (cm)", max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    height_cm = models.DecimalField("alto (cm)", max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    active = models.BooleanField("activa", default=True)

    class Meta:
        ordering = ["product__name", "sku"]
        verbose_name = "variante"
        verbose_name_plural = "variantes"
        constraints = [
            models.CheckConstraint(condition=Q(sale_price__isnull=True) | Q(sale_price__lte=models.F("price")), name="sale_not_over_price")
        ]

    def __str__(self):
        return f"{self.product.name} — {self.name or self.sku}"

    @property
    def current_price(self):
        return self.sale_price if self.sale_price is not None else self.price

    @property
    def has_shipping_dimensions(self):
        return self.product.has_shipping_dimensions or all([
            self.weight_kg, self.length_cm, self.width_cm, self.height_cm,
        ])


class InventoryAdjustment(models.Model):
    class Reason(models.TextChoices):
        INITIAL = "initial", "Inventario inicial"
        RESTOCK = "restock", "Entrada manual"
        CORRECTION = "correction", "Corrección"
        DAMAGE = "damage", "Daño o merma"
        LOSS = "loss", "Pérdida"
        COUNT = "count", "Conteo físico"
        EXTERNAL_SALE = "external_sale", "Venta externa"
        ONLINE_SALE = "online_sale", "Venta en línea"
        CANCELLATION = "cancellation", "Cancelación"
        RETURN = "return", "Devolución"

    variant = models.ForeignKey(Variant, on_delete=models.PROTECT, related_name="inventory_adjustments")
    delta = models.IntegerField("cambio")
    reason = models.CharField("motivo", max_length=30, choices=Reason.choices)
    reference = models.CharField("referencia", max_length=120, blank=True)
    notes = models.TextField("notas", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "movimiento de inventario"
        verbose_name_plural = "movimientos de inventario"

    def __str__(self):
        return f"{self.variant.sku}: {self.delta:+d} ({self.get_reason_display()})"


class Cart(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Activo"
        CONVERTED = "converted", "Convertido"
        ABANDONED = "abandoned", "Abandonado"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="carts")
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user"], condition=Q(status="active", user__isnull=False), name="one_active_cart_per_user"),
            models.UniqueConstraint(fields=["session_key"], condition=Q(status="active") & ~Q(session_key=""), name="one_active_cart_per_session"),
        ]

    @property
    def subtotal(self):
        return sum((item.total for item in self.items.select_related("variant")), Decimal("0"))

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        constraints = [models.UniqueConstraint(fields=["cart", "variant"], name="unique_variant_per_cart")]

    @property
    def total(self):
        return self.variant.current_price * self.quantity


class Order(TimeStampedModel):
    class Source(models.TextChoices):
        ONLINE = "online", "Tienda en línea"
        ADMIN = "admin", "Venta externa"

    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pendiente de pago"
        PAID = "paid", "Pagado"
        PREPARING = "preparing", "Preparando"
        SHIPPED = "shipped", "Enviado"
        READY_PICKUP = "ready_pickup", "Listo para recolección"
        COMPLETED = "completed", "Completado"
        CANCELLED = "cancelled", "Cancelado"
        PAYMENT_FAILED = "payment_failed", "Pago rechazado"
        EXPIRED = "expired", "Pago vencido"

    class Fulfillment(models.TextChoices):
        SHIPPING = "shipping", "Envío a domicilio"
        PICKUP = "pickup", "Recolección"

    number = models.CharField("folio", max_length=24, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    source = models.CharField("origen", max_length=12, choices=Source.choices, default=Source.ONLINE)
    status = models.CharField("estado", max_length=30, choices=Status.choices, default=Status.PENDING_PAYMENT)
    customer_name = models.CharField("cliente", max_length=160)
    customer_email = models.EmailField("correo")
    customer_phone = models.CharField("teléfono", max_length=20)
    fulfillment = models.CharField("entrega", max_length=12, choices=Fulfillment.choices)
    pickup_location = models.ForeignKey(StoreLocation, null=True, blank=True, on_delete=models.PROTECT, related_name="pickup_orders")
    shipping_address = models.JSONField("dirección de envío", default=dict, blank=True)
    carrier = models.CharField("paquetería", max_length=80, blank=True)
    shipping_service = models.CharField("servicio de envío", max_length=100, blank=True)
    shipping_rate_id = models.CharField("id de tarifa", max_length=160, blank=True)
    tracking_number = models.CharField("guía", max_length=120, blank=True)
    tracking_url = models.URLField("URL de rastreo", max_length=600, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_amount = models.DecimalField("envío", max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_expires_at = models.DateTimeField("vence bloqueo de stock", null=True, blank=True)
    stock_released = models.BooleanField(default=False)
    notes = models.TextField("notas", blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = f"AGA-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(Variant, null=True, blank=True, on_delete=models.SET_NULL, related_name="order_items")
    sku = models.CharField(max_length=100)
    product_name = models.CharField("producto", max_length=180)
    variant_name = models.CharField("variante", max_length=120, blank=True)
    attributes = models.JSONField("opciones", default=dict, blank=True)
    unit_price = models.DecimalField("precio unitario", max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField("cantidad")

    @property
    def total(self):
        return self.unit_price * self.quantity


class Payment(TimeStampedModel):
    class Provider(models.TextChoices):
        MERCADO_PAGO = "mercado_pago", "Mercado Pago"
        MANUAL = "manual", "Registro manual"

    class Method(models.TextChoices):
        MERCADO_PAGO = "mercado_pago", "Mercado Pago"
        CASH = "cash", "Efectivo"
        TRANSFER = "transfer", "Transferencia"
        EXTERNAL_CARD = "external_card", "Tarjeta cobrada fuera del sistema"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        APPROVED = "approved", "Aprobado"
        REJECTED = "rejected", "Rechazado"
        CANCELLED = "cancelled", "Cancelado"
        REFUNDED = "refunded", "Reembolsado"

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    provider = models.CharField(max_length=30, choices=Provider.choices)
    method = models.CharField("método", max_length=30, choices=Method.choices)
    status = models.CharField("estado", max_length=20, choices=Status.choices, default=Status.PENDING)
    external_id = models.CharField("referencia externa", max_length=160, blank=True, db_index=True)
    amount = models.DecimalField("monto", max_digits=12, decimal_places=2)
    currency = models.CharField("moneda", max_length=3, default="MXN")
    card_brand = models.CharField("marca de tarjeta", max_length=40, blank=True)
    card_last4 = models.CharField("últimos 4 dígitos", max_length=4, blank=True)
    paid_at = models.DateTimeField("fecha de pago", null=True, blank=True)
    provider_response = models.JSONField("respuesta no sensible", default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "pago"
        verbose_name_plural = "pagos"

    def clean(self):
        if self.card_last4 and (len(self.card_last4) != 4 or not self.card_last4.isdigit()):
            raise ValidationError({"card_last4": "Guarda únicamente cuatro dígitos."})

