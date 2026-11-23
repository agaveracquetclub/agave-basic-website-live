from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from store.forms import AddressForm, CheckoutForm
from store.models import Cart, CartItem, Product, StoreLocation, Variant
from store.services.shipping import build_packages, package_summary


class PackingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("packing", password="test-password")
        self.cart = Cart.objects.create(user=self.user)

    def make_racket(self, slug, sku):
        product = Product.objects.create(
            name=slug, slug=slug, category="Raquetas", show_in_catalog=True,
            package_weight_kg=Decimal("0.400"), package_length_cm=Decimal("65"),
            package_width_cm=Decimal("30"), package_height_cm=Decimal("10"),
            units_per_package=2,
        )
        return Variant.objects.create(product=product, sku=sku, price=Decimal("1000"), stock=5)

    def test_two_compatible_rackets_share_one_box(self):
        first = self.make_racket("raqueta-uno", "R-1")
        second = self.make_racket("raqueta-dos", "R-2")
        CartItem.objects.create(cart=self.cart, variant=first, quantity=1)
        CartItem.objects.create(cart=self.cart, variant=second, quantity=1)

        packages = build_packages(self.cart)
        summary = package_summary(packages)

        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0]["weight"], 0.8)
        self.assertEqual(packages[0]["_volumetric_weight"], Decimal("3.900"))
        self.assertEqual(summary["boxes"], 1)
        self.assertEqual(summary["billable_weight_kg"], "3.900")

    def test_three_rackets_use_two_boxes(self):
        racket = self.make_racket("raqueta-tres", "R-3")
        CartItem.objects.create(cart=self.cart, variant=racket, quantity=3)
        self.assertEqual(len(build_packages(self.cart)), 2)


class CatalogAndAddressTests(TestCase):
    def test_address_country_is_temporarily_mexico_only(self):
        self.assertEqual(AddressForm().fields["country_code"].choices, [("MX", "México")])

    def test_seed_uses_verified_catalog_image_counts(self):
        call_command("seed_catalog", verbosity=0)
        self.assertEqual(Product.objects.filter(show_in_catalog=True).count(), 7)
        self.assertEqual(Product.objects.filter(category="Palas de pádel", show_in_catalog=True).count(), 4)
        for slug in [
            "raqueta-general-negra-97",
            "raqueta-general-blanca-103",
            "raqueta-general-azul-100",
        ]:
            self.assertEqual(Product.objects.get(slug=slug).images.count(), 8)
        for slug in [
            "babolat-viper-3k-azul-2026",
            "babolat-viper-3k-naranja-2026",
        ]:
            self.assertEqual(Product.objects.get(slug=slug).images.count(), 14)
        for slug in [
            "nox-at10-luxury-genius-12k-2026",
            "nox-at10-luxury-genius-18k-2026",
        ]:
            self.assertEqual(Product.objects.get(slug=slug).images.count(), 0)

        white = Product.objects.get(slug="raqueta-general-blanca-103")
        self.assertEqual(white.name, "Wilson Pro Staff Precision Team 103")
        self.assertEqual(white.brand, "WILSON")
        self.assertEqual(white.authenticity, Product.Authenticity.VERIFIED)

    def test_pickup_choices_show_full_address(self):
        location = StoreLocation.objects.create(
            name="Puebla — La Paz",
            street_address="9 Poniente 2709",
            neighborhood="La Paz",
            city="Puebla",
            state="Puebla",
            postal_code="72160",
            pickup_enabled=True,
        )
        field = CheckoutForm().fields["pickup_location"]
        self.assertIn("9 Poniente 2709", field.label_from_instance(location))
