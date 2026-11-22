from django.db import migrations


def gallery(stem, count, extension):
    return [f"/static/store/img/products/{stem}-{index:02d}.{extension}" for index in range(1, count + 1)]


GALLERIES = {
    "raqueta-general-negra-97": gallery("raqueta-general-negra-97", 13, "jpeg"),
    "raqueta-general-blanca-103": gallery("raqueta-general-blanca-103", 8, "jpeg"),
    "raqueta-general-azul-100": gallery("raqueta-general-azul-100", 16, "jpeg"),
    "nox-at10-luxury-genius-12k-2026": gallery("nox-at10-12k", 3, "png"),
    "nox-at10-luxury-genius-18k-2026": gallery("nox-at10-18k", 3, "png"),
    "babolat-viper-3k-azul-2026": ["/static/store/img/products/babolat-viper-azul.jpg"],
    "babolat-viper-3k-naranja-2026": ["/static/store/img/products/babolat-viper-naranja.jpg"],
}


def repair_galleries(apps, schema_editor):
    Product = apps.get_model("store", "Product")
    ProductImage = apps.get_model("store", "ProductImage")
    for slug, paths in GALLERIES.items():
        product = Product.objects.filter(slug=slug).first()
        if not product:
            continue
        ProductImage.objects.filter(
            product=product,
            external_url__startswith="https://drive.google.com/",
        ).delete()
        ProductImage.objects.filter(
            product=product,
            external_url__startswith="/static/store/img/products/",
        ).exclude(external_url__in=paths).delete()
        for position, path in enumerate(paths):
            image, _ = ProductImage.objects.get_or_create(
                product=product,
                external_url=path,
                defaults={
                    "position": position,
                    "alt_text": f"{product.name} — foto {position + 1}",
                },
            )
            image.position = position
            image.alt_text = f"{product.name} — foto {position + 1}"
            image.save(update_fields=["position", "alt_text", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [("store", "0005_remove_product_unverified_product_stays_hidden_and_more")]

    operations = [migrations.RunPython(repair_galleries, migrations.RunPython.noop)]
