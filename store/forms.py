from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.forms import formset_factory, inlineformset_factory

from .models import Address, InventoryAdjustment, Order, Product, ProductImage, StoreLocation, Variant


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellidos", max_length=150)
    phone = forms.CharField(label="Teléfono", max_length=20)

    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email", "phone", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = user.customer_profile
            profile.phone = self.cleaned_data["phone"]
            profile.save(update_fields=["phone", "updated_at"])
        return user


class AddToCartForm(forms.Form):
    variant_id = forms.ModelChoiceField(queryset=Variant.objects.none(), empty_label=None)
    quantity = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        if product:
            self.fields["variant_id"].queryset = product.variants.filter(active=True)
            self.fields["variant_id"].label_from_instance = lambda v: f"{v.name or v.sku} — ${v.current_price:,.2f} ({v.stock} disponibles)"


class CartQuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=0, max_value=99)


class AddressForm(forms.ModelForm):
    country_code = forms.ChoiceField(
        label="País",
        choices=[("MX", "México")],
        initial="MX",
    )

    class Meta:
        model = Address
        exclude = ("user",)


class CheckoutForm(forms.Form):
    fulfillment = forms.ChoiceField(choices=Order.Fulfillment.choices, widget=forms.RadioSelect)
    address = forms.ModelChoiceField(queryset=Address.objects.none(), required=False)
    pickup_location = forms.ModelChoiceField(queryset=StoreLocation.objects.none(), required=False)
    shipping_rate_id = forms.CharField(required=False, widget=forms.HiddenInput)
    carrier = forms.CharField(required=False, widget=forms.HiddenInput)
    shipping_service = forms.CharField(required=False, widget=forms.HiddenInput)
    shipping_amount = forms.DecimalField(required=False, min_value=0, widget=forms.HiddenInput)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields["address"].queryset = user.addresses.all()
        self.fields["pickup_location"].queryset = StoreLocation.objects.filter(active=True, pickup_enabled=True)

    def clean(self):
        cleaned = super().clean()
        fulfillment = cleaned.get("fulfillment")
        if fulfillment == Order.Fulfillment.SHIPPING and not cleaned.get("address"):
            self.add_error("address", "Selecciona una dirección de envío.")
        if fulfillment == Order.Fulfillment.PICKUP and not cleaned.get("pickup_location"):
            self.add_error("pickup_location", "Selecciona un punto de recolección.")
        return cleaned


class ExternalSaleHeaderForm(forms.Form):
    customer_name = forms.CharField(label="Cliente", max_length=160)
    customer_email = forms.EmailField(label="Correo", required=False)
    customer_phone = forms.CharField(label="Teléfono", max_length=20, required=False)
    payment_method = forms.ChoiceField(
        label="Método de pago",
        choices=[("cash", "Efectivo"), ("transfer", "Transferencia"), ("external_card", "Tarjeta cobrada fuera del sistema")],
    )
    notes = forms.CharField(label="Notas", widget=forms.Textarea(attrs={"rows": 3}), required=False)


class ExternalSaleLineForm(forms.Form):
    variant = forms.ModelChoiceField(label="Producto / variante", queryset=Variant.objects.filter(active=True).select_related("product"))
    quantity = forms.IntegerField(label="Cantidad", min_value=1, initial=1)


ExternalSaleLineFormSet = formset_factory(ExternalSaleLineForm, extra=3, min_num=1, validate_min=True, can_delete=True)


class OwnerProductForm(forms.ModelForm):
    sports_text = forms.CharField(
        label="Deportes",
        required=False,
        help_text="Separados por comas. Ejemplo: tenis, pádel",
    )
    specifications_json = forms.JSONField(
        label="Especificaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 7}),
        help_text='Formato JSON. Ejemplo: {"peso_g": 300, "color": "Negro"}',
    )

    class Meta:
        model = Product
        fields = (
            "name", "slug", "brand", "description", "category", "authenticity",
            "show_in_catalog", "featured", "package_weight_kg", "package_length_cm",
            "package_width_cm", "package_height_cm", "units_per_package",
        )
        widgets = {"description": forms.Textarea(attrs={"rows": 7})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["sports_text"].initial = ", ".join(self.instance.sports or [])
            self.fields["specifications_json"].initial = self.instance.specifications or {}

    def save(self, commit=True):
        product = super().save(commit=False)
        product.sports = [item.strip() for item in self.cleaned_data.get("sports_text", "").split(",") if item.strip()]
        product.specifications = self.cleaned_data.get("specifications_json") or {}
        if commit:
            product.save()
        return product


class OwnerProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ("image", "external_url", "alt_text", "position")


OwnerProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=OwnerProductImageForm,
    extra=1,
    can_delete=False,
)


class OwnerVariantForm(forms.ModelForm):
    class Meta:
        model = Variant
        fields = (
            "sku", "name", "attributes", "price", "sale_price", "low_stock_threshold",
            "active",
        )
        widgets = {"attributes": forms.Textarea(attrs={"rows": 5})}


class StockAdjustmentForm(forms.Form):
    class Operation:
        ADD = "add"
        REMOVE = "remove"
        SET = "set"

    variant = forms.ModelChoiceField(
        label="Variante",
        queryset=Variant.objects.select_related("product").order_by("product__name", "name", "sku"),
    )
    operation = forms.ChoiceField(
        label="Operación",
        choices=[
            (Operation.ADD, "Recibir / sumar unidades"),
            (Operation.REMOVE, "Retirar unidades"),
            (Operation.SET, "Establecer conteo físico"),
        ],
    )
    quantity = forms.IntegerField(label="Cantidad", min_value=0)
    reason = forms.ChoiceField(
        label="Motivo",
        choices=[
            (InventoryAdjustment.Reason.RESTOCK, "Recepción de mercancía"),
            (InventoryAdjustment.Reason.COUNT, "Conteo físico"),
            (InventoryAdjustment.Reason.CORRECTION, "Corrección"),
            (InventoryAdjustment.Reason.DAMAGE, "Daño o merma"),
            (InventoryAdjustment.Reason.LOSS, "Pérdida"),
            (InventoryAdjustment.Reason.RETURN, "Devolución del cliente"),
        ],
    )
    reference = forms.CharField(
        label="Referencia",
        max_length=120,
        required=False,
        help_text="Factura, nota, proveedor o folio relacionado.",
    )
    notes = forms.CharField(label="Notas", required=False, widget=forms.Textarea(attrs={"rows": 4}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("operation") != self.Operation.SET and cleaned.get("quantity") == 0:
            self.add_error("quantity", "Para sumar o retirar, la cantidad debe ser mayor que cero.")
        return cleaned

