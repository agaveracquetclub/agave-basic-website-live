from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import Product, ProductImage, StoreLocation, Variant


def local_gallery(stem, count, extension):
    return [f"/static/store/img/products/{stem}-{index:02d}.{extension}" for index in range(1, count + 1)]


CATALOG = [
    {
        "slug": "raqueta-general-negra-97",
        "name": "Raqueta General Negra 97",
        "brand": "Agave / Genérica",
        "category": "Raquetas de tenis",
        "sports": ["tenis"],
        "description": "Raqueta general negra para jugadores que buscan control y una sensación firme. Producto genérico; no se comercializa como artículo oficial de otra marca.",
        "specifications": {"peso_g": 315, "cabeza_in2": 97, "mango": "L2 (4 1/4)", "color": "Negro", "patron": "16x19", "balance_mm": 310},
        "sku": "TEN-GEN-NEGRA-97-L2",
        "variant": "Mango L2 / Negra",
        "price": "5499.00",
        "sale_price": "2999.00",
        "images": local_gallery("raqueta-general-negra-97", 13, "jpeg"),
        "publish": True,
        "authenticity": Product.Authenticity.GENERIC,
    },
    {
        "slug": "raqueta-general-blanca-103",
        "name": "Raqueta General Blanca 103",
        "brand": "Agave / Genérica",
        "category": "Raquetas de tenis",
        "sports": ["tenis"],
        "description": "Raqueta general blanca con cabeza amplia, pensada para comodidad y facilidad de juego. Producto genérico; no se comercializa como artículo oficial de otra marca.",
        "specifications": {"peso_g": 299, "cabeza_in2": 103, "mango": "L2 (4 1/4)", "color": "Blanco", "patron": "16x19", "balance_mm": 330},
        "sku": "TEN-GEN-BLANCA-103-L2",
        "variant": "Mango L2 / Blanca",
        "price": "2599.00",
        "sale_price": "1999.00",
        "images": local_gallery("raqueta-general-blanca-103", 8, "jpeg"),
        "publish": True,
        "authenticity": Product.Authenticity.GENERIC,
    },
    {
        "slug": "raqueta-general-azul-100",
        "name": "Raqueta General Azul 100",
        "brand": "Agave / Genérica",
        "category": "Raquetas de tenis",
        "sports": ["tenis"],
        "description": "Raqueta general azul con equilibrio entre potencia, comodidad y control. Producto genérico; no se comercializa como artículo oficial de otra marca.",
        "specifications": {"peso_g": 300, "cabeza_in2": 100, "mango": "L2 (4 1/4)", "color": "Azul", "patron": "16x19", "balance_mm": 320},
        "sku": "TEN-GEN-AZUL-100-L2",
        "variant": "Mango L2 / Azul",
        "price": "4999.00",
        "sale_price": "2999.00",
        "images": local_gallery("raqueta-general-azul-100", 16, "jpeg"),
        "publish": True,
        "authenticity": Product.Authenticity.GENERIC,
    },
    {
        "slug": "nox-at10-luxury-genius-12k-2026",
        "name": "Nox AT10 Luxury Genius 12K Alum Xtrem 2026",
        "brand": "NOX",
        "category": "Palas de pádel",
        "sports": ["pádel"],
        "description": "Pala de pádel de formato lágrima con balance polivalente, superficie de carbono 12K Alum XTREM y núcleo HR3 Black EVA. Adecuada para jugadores que buscan combinar potencia, control y un tacto firme.",
        "specifications": {"peso_g": "360-375", "perfil_mm": 38, "forma": "Lágrima", "color": "Blanco con dorado"},
        "sku": "PAD-PA-NO-LG-12K-BL",
        "variant": "Blanco con dorado",
        "price": "6999.00",
        "sale_price": "3499.00",
        "images": local_gallery("nox-at10-12k", 3, "png"),
        "publish": True,
        "authenticity": Product.Authenticity.UNVERIFIED,
    },
    {
        "slug": "nox-at10-luxury-genius-18k-2026",
        "name": "Nox AT10 Luxury Genius 18K Alum 2026",
        "brand": "NOX",
        "category": "Palas de pádel",
        "sports": ["pádel"],
        "description": "Pala de pádel de formato lágrima con balance medio-alto, caras de carbono 18K Alum y núcleo MLD Black EVA. Pensada para un juego polivalente con potencia, precisión y control.",
        "specifications": {"peso_g": "360-375", "perfil_mm": 38, "forma": "Lágrima", "color": "Negro con dorado"},
        "sku": "PAD-PA-NO-LG-18K-NE",
        "variant": "Negro con dorado",
        "price": "6999.00",
        "sale_price": "3499.00",
        "images": local_gallery("nox-at10-18k", 3, "png"),
        "publish": True,
        "authenticity": Product.Authenticity.UNVERIFIED,
    },
    {
        "slug": "babolat-viper-3k-azul-2026",
        "name": "Babolat Viper 3K Azul 2026",
        "brand": "BABOLAT",
        "category": "Palas de pádel",
        "sports": ["pádel"],
        "description": "Pala de pádel de formato diamante y balance alto, orientada a jugadores ofensivos que buscan potencia, estabilidad y generación de efectos.",
        "specifications": {"peso_g": "370 ± 10", "perfil_mm": 38, "forma": "Diamante", "color": "Azul con verde"},
        "sku": "PAD-PA-BA-VI-3K-AZ",
        "variant": "Azul con verde",
        "price": "6999.00",
        "sale_price": "3499.00",
        "images": ["/static/store/img/products/babolat-viper-azul.jpg"],
        "publish": True,
        "authenticity": Product.Authenticity.UNVERIFIED,
    },
    {
        "slug": "babolat-viper-3k-naranja-2026",
        "name": "Babolat Viper 3K Naranja 2026",
        "brand": "BABOLAT",
        "category": "Palas de pádel",
        "sports": ["pádel"],
        "description": "Pala de pádel de formato diamante y balance alto, orientada a jugadores ofensivos que buscan potencia, estabilidad y generación de efectos.",
        "specifications": {"peso_g": "370 ± 10", "perfil_mm": 38, "forma": "Diamante", "color": "Naranja"},
        "sku": "PAD-PA-BA-VI-3K-NA",
        "variant": "Naranja",
        "price": "6999.00",
        "sale_price": "3499.00",
        "images": ["/static/store/img/products/babolat-viper-naranja.jpg"],
        "publish": True,
        "authenticity": Product.Authenticity.UNVERIFIED,
    },
]


class Command(BaseCommand):
    help = "Carga el catálogo inicial y las ubicaciones sin inventar existencias ni medidas."

    @transaction.atomic
    def handle(self, *args, **options):
        locations = [
            {
                "name": "Puebla — Origen temporal de envíos",
                "street_address": "11 Poniente 2707",
                "neighborhood": "",
                "city": "Puebla",
                "state": "Puebla",
                "postal_code": "",
                "pickup_enabled": False,
                "is_shipping_origin": True,
            },
            {
                "name": "Puebla — La Paz",
                "street_address": "9 Poniente 2709",
                "neighborhood": "La Paz",
                "city": "Puebla",
                "state": "Puebla",
                "postal_code": "",
                "pickup_enabled": True,
                "is_shipping_origin": False,
            },
            {
                "name": "Orizaba — Centro / La Concordia",
                "street_address": "Oriente 5 esquina con Norte 28 #1500",
                "neighborhood": "Centro / La Concordia",
                "city": "Orizaba",
                "state": "Veracruz",
                "postal_code": "94300",
                "pickup_enabled": True,
                "is_shipping_origin": False,
            },
        ]
        StoreLocation.objects.filter(is_shipping_origin=True).update(is_shipping_origin=False)
        for values in locations:
            StoreLocation.objects.update_or_create(name=values["name"], defaults=values)

        for row in CATALOG:
            product, _ = Product.objects.update_or_create(
                slug=row["slug"],
                defaults={
                    "name": row["name"], "brand": row["brand"], "category": row["category"],
                    "sports": row["sports"], "description": row["description"],
                    "specifications": row["specifications"], "authenticity": row["authenticity"],
                    "show_in_catalog": row["publish"],
                    "package_weight_kg": Decimal("0.400"),
                    "package_length_cm": Decimal("65.00"),
                    "package_width_cm": Decimal("30.00"),
                    "package_height_cm": Decimal("10.00"),
                    "units_per_package": 2,
                },
            )
            Variant.objects.update_or_create(
                sku=row["sku"],
                defaults={
                    "product": product, "name": row["variant"], "price": Decimal(row["price"]),
                    "sale_price": Decimal(row["sale_price"]) if row.get("sale_price") else None,
                },
            )
            expected_images = set(row.get("images", []))
            product.images.filter(external_url__startswith="https://drive.google.com/").delete()
            product.images.filter(external_url__startswith="/static/store/img/products/").exclude(
                external_url__in=expected_images
            ).delete()
            for position, image_url in enumerate(row.get("images", [])):
                image = ProductImage.objects.filter(product=product, external_url=image_url).first()
                if image:
                    image.position = position
                    image.alt_text = f"{row['name']} — foto {position + 1}"
                    image.save(update_fields=["position", "alt_text", "updated_at"])
                else:
                    ProductImage.objects.create(
                        product=product,
                        position=position,
                        external_url=image_url,
                        alt_text=f"{row['name']} — foto {position + 1}",
                    )
        self.stdout.write(self.style.SUCCESS("Catálogo y ubicaciones cargados. Completa inventario, medidas, teléfonos y CP desde el panel."))

