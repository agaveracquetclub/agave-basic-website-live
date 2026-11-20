from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import Product, ProductImage, StoreLocation, Variant


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
        "images": [
            "/static/store/img/products/raqueta-general-negra-97.jpg",
            "https://drive.google.com/uc?export=view&id=1SocqxuGf8PUzY_e4Ls6R6lPN0Y4u_QKv",
            "https://drive.google.com/uc?export=view&id=1CKmJVYsi0qlHn0hKrYrufM1qBZEA-vPW",
            "https://drive.google.com/uc?export=view&id=1Yl5oLmsxsIqNwYFbcklDHq4SXkLTl9tO",
            "https://drive.google.com/uc?export=view&id=1pSbZjPMNdDGE0pRnkqtMXofPTW1GiOKJ",
            "https://drive.google.com/uc?export=view&id=1K_t67a45u0kBX6H1VF-HTpKiUM_p89J3",
            "https://drive.google.com/uc?export=view&id=1id2_kJHDT5SB4J8Xz1taZm9xHcLsN5I7",
        ],
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
        "images": [
            "/static/store/img/products/raqueta-general-blanca-103.jpg",
            "https://drive.google.com/uc?export=view&id=1bLF9FcxZ8ybiVZ9qw0JpKWJzuLt0-PIe",
            "https://drive.google.com/uc?export=view&id=1ZaTuf7WMqaYj_GwTZE7dWrhWsC-vXhPx",
            "https://drive.google.com/uc?export=view&id=1d8sUK_ZEa_tpV3bAYfk9TEInCnf_N_LJ",
            "https://drive.google.com/uc?export=view&id=1-QnDolCgt-OG0zfCrV0rioyrjlfflOhq",
            "https://drive.google.com/uc?export=view&id=1XPACldP6IztAlncOdWOgTFar_ovXULp4",
            "https://drive.google.com/uc?export=view&id=1HBbxeMZtFw-HFg69IQjEmhKVlrYp8uOf",
            "https://drive.google.com/uc?export=view&id=1ZovENP2S1JfhGCPS1r2KnOubJUAxeEEt",
        ],
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
        "images": [
            "/static/store/img/products/raqueta-general-azul-100.jpg",
            "https://drive.google.com/uc?export=view&id=1QRTsZg6h8cDehsvowichSM6dpYkksld9",
            "https://drive.google.com/uc?export=view&id=1MEubTxhxYpbdot7g9Bkodzach3R69rET",
            "https://drive.google.com/uc?export=view&id=14rA4-1GgcCqfDyUe5y8SYoyq9ZASRm8h",
            "https://drive.google.com/uc?export=view&id=1A9AJ_HaEM88RkylP7F1_ahxtX3thuMu8",
            "https://drive.google.com/uc?export=view&id=1e-2yAQHakxBHQ5hnFsBU79qEcHsVs9A4",
            "https://drive.google.com/uc?export=view&id=1oa_ZdSSSitgefXy2L9eAUVkMYhtG1lAu",
            "https://drive.google.com/uc?export=view&id=1Edjfw9UeJ0LVDqBGg6e_Rook2aE3LQvj",
        ],
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
        "images": [
            "/static/store/img/products/nox-at10-12k.jpg",
            "https://drive.google.com/uc?export=view&id=1y5dKCqCy3rTfDm-46X1cQRSYoDe8Gav0",
            "https://drive.google.com/uc?export=view&id=1JVa1RFzhT6TSmbXfUpuZb0PenHyO61Sg",
        ],
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
        "images": [
            "/static/store/img/products/nox-at10-18k.jpg",
            "https://drive.google.com/uc?export=view&id=1J4hCnlNV85XDkqYFpaAhZjFYvmhZk1UK",
            "https://drive.google.com/uc?export=view&id=1A93VSX0GHcxdwJj3z3Kvu2kyDpqMAtBL",
        ],
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

