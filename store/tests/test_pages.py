from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from store.models import Product, Variant


class PublicPageTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Raqueta General", slug="raqueta-general", brand="Agave / Genérica",
            category="Raquetas de tenis", show_in_catalog=True,
        )
        Variant.objects.create(product=self.product, sku="GEN-1", price=Decimal("999.00"), stock=3)

    def test_home_and_catalog_render(self):
        self.assertEqual(self.client.get(reverse("store:home")).status_code, 200)
        response = self.client.get(reverse("store:catalog"))
        self.assertContains(response, "Raqueta General")

    def test_product_detail_renders_variant(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, "GEN-1")

    def test_logged_in_customer_can_return_home(self):
        user = get_user_model().objects.create_user("visitante", password="test-password")
        self.client.force_login(user)
        response = self.client.get(reverse("store:home"))
        self.assertContains(response, "Inicio")
        self.assertContains(response, "Preguntas frecuentes")

