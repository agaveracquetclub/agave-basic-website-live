from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("store", "0006_repair_seeded_product_galleries")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="discount_percent",
            field=models.DecimalField(
                blank=True, decimal_places=2,
                help_text="Opcional. Se compara con otras promociones; los descuentos no se acumulan.",
                max_digits=5, null=True,
                validators=[MinValueValidator(Decimal("0"))],
                verbose_name="descuento del producto (%)",
            ),
        ),
        migrations.CreateModel(
            name="StoreSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("global_discount_percent", models.DecimalField(blank=True, decimal_places=2, help_text="Se aplica a toda la tienda. No se acumula con otras ofertas; siempre gana el menor precio.", max_digits=5, null=True, validators=[MinValueValidator(Decimal("0"))], verbose_name="descuento global (%)")),
                ("promotion_name", models.CharField(blank=True, max_length=120, verbose_name="nombre de la promoción")),
                ("promotion_active", models.BooleanField(default=False, verbose_name="promoción activa")),
            ],
            options={"verbose_name": "configuración de la tienda", "verbose_name_plural": "configuración de la tienda"},
        ),
    ]
