from django.db import migrations, models


PRODUCT_UPDATES = {
    "raqueta-general-negra-97": ("Raqueta Profesional Negra 97", "Pro Staff V13 97"),
    "raqueta-general-blanca-103": ("Raqueta Profesional Blanca 103", "Wilson Pro Staff Precision Team 103"),
    "raqueta-general-azul-100": ("Raqueta Profesional Azul 100", "Yonex Ezone 100"),
}


def update_catalog(apps, schema_editor):
    Product = apps.get_model("store", "Product")
    ProductImage = apps.get_model("store", "ProductImage")
    StoreLocation = apps.get_model("store", "StoreLocation")
    for slug, (name, reference) in PRODUCT_UPDATES.items():
        Product.objects.filter(slug=slug).update(name=name, reference_model_name=reference)
    StoreLocation.objects.filter(street_address="11 Poniente 2707").update(
        neighborhood="La Paz",
        postal_code="72160",
        phone="2721255835",
        contact_name="Agave Racquet Club",
        contact_email="agaveracquetclub@gmail.com",
    )
    galleries = {
        "babolat-viper-3k-azul-2026": "babolat-viper-azul",
        "babolat-viper-3k-naranja-2026": "babolat-viper-naranja",
    }
    for slug, stem in galleries.items():
        product = Product.objects.filter(slug=slug).first()
        if not product:
            continue
        ProductImage.objects.filter(product=product).delete()
        ProductImage.objects.bulk_create([
            ProductImage(
                product=product,
                position=index - 1,
                external_url=f"/static/store/img/products/{stem}-{index:02d}.jpg",
                alt_text=f"{product.name} — foto {index}",
            )
            for index in range(1, 15)
        ])


def reverse_catalog(apps, schema_editor):
    Product = apps.get_model("store", "Product")
    reverse_names = {
        "raqueta-general-negra-97": "Raqueta General Negra 97",
        "raqueta-general-blanca-103": "Raqueta General Blanca 103",
        "raqueta-general-azul-100": "Raqueta General Azul 100",
    }
    for slug, name in reverse_names.items():
        Product.objects.filter(slug=slug).update(name=name, reference_model_name="")


class Migration(migrations.Migration):
    dependencies = [("store", "0007_product_discount_and_store_settings")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="reference_model_name",
            field=models.CharField(
                blank=True,
                help_text="Solo para control interno. No se muestra al cliente ni sustituye el nombre comercial.",
                max_length=180,
                verbose_name="modelo de referencia interno",
            ),
        ),
        migrations.RunPython(update_catalog, reverse_catalog),
    ]
