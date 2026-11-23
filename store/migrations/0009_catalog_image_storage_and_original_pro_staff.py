from decimal import Decimal

from django.db import migrations


IMAGE_BASE = "https://lhzpojsvadkbvicdwnun.supabase.co/storage/v1/object/public/agave-products/catalog"


GALLERIES = {
    "raqueta-general-negra-97": ("raqueta-general-negra-97", 8, "jpeg"),
    "raqueta-general-blanca-103": ("raqueta-general-blanca-103", 8, "jpeg"),
    "raqueta-general-azul-100": ("raqueta-general-azul-100", 8, "jpeg"),
    "babolat-viper-3k-azul-2026": ("babolat-viper-azul", 14, "jpg"),
    "babolat-viper-3k-naranja-2026": ("babolat-viper-naranja", 14, "jpg"),
}


def apply_catalog_corrections(apps, schema_editor):
    Product = apps.get_model("store", "Product")
    ProductImage = apps.get_model("store", "ProductImage")
    Variant = apps.get_model("store", "Variant")

    white = Product.objects.filter(slug="raqueta-general-blanca-103").first()
    if white:
        white.name = "Wilson Pro Staff Precision Team 103"
        white.brand = "WILSON"
        white.reference_model_name = ""
        white.authenticity = "verified"
        white.description = (
            "Raqueta Wilson Pro Staff Precision Team 103 original, con cabeza de 103 in² "
            "y patrón de encordado 16x19. Su cabeza amplia favorece la comodidad y la facilidad de juego."
        )
        white.save(update_fields=[
            "name", "brand", "reference_model_name", "authenticity", "description", "updated_at"
        ])

    tennis_slugs = [
        "raqueta-general-negra-97",
        "raqueta-general-blanca-103",
        "raqueta-general-azul-100",
    ]
    Variant.objects.filter(product__slug__in=tennis_slugs).update(
        price=Decimal("3999.00"), sale_price=Decimal("2999.00")
    )

    ProductImage.objects.filter(
        product__slug__in=[
            "nox-at10-luxury-genius-12k-2026",
            "nox-at10-luxury-genius-18k-2026",
        ]
    ).delete()

    for slug, (stem, count, extension) in GALLERIES.items():
        product = Product.objects.filter(slug=slug).first()
        if not product:
            continue
        ProductImage.objects.filter(product=product).delete()
        ProductImage.objects.bulk_create([
            ProductImage(
                product=product,
                position=index - 1,
                external_url=f"{IMAGE_BASE}/{stem}-{index:02d}.{extension}",
                alt_text=f"{product.name} — foto {index}",
            )
            for index in range(1, count + 1)
        ])


class Migration(migrations.Migration):
    dependencies = [("store", "0008_product_reference_and_catalog_names")]

    operations = [migrations.RunPython(apply_catalog_corrections, migrations.RunPython.noop)]
