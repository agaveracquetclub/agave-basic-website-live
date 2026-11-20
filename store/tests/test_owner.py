from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from store.models import InventoryAdjustment, Product, Variant


class OwnerInterfaceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_superuser("dueno", "dueno@example.com", "owner-test-password")
        self.customer = user_model.objects.create_user("cliente2", "cliente2@example.com", "customer-test-password")
        self.product = Product.objects.create(
            name="Producto del dueño", slug="producto-dueno", brand="Agave / Genérica",
            category="Raquetas de tenis", authenticity=Product.Authenticity.GENERIC,
            show_in_catalog=True,
        )
        self.variant = Variant.objects.create(
            product=self.product, sku="OWNER-001", name="Única",
            price=Decimal("1200.00"), stock=4,
        )

    def test_only_superuser_can_open_owner_dashboard(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("store:owner_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.owner)
        response = self.client.get(reverse("store:owner_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resumen del negocio")

    def test_archive_is_soft_and_disables_variants(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("store:owner_product_archive", args=[self.product.pk]))
        self.assertRedirects(response, reverse("store:owner_products"))
        self.product.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertFalse(self.product.show_in_catalog)
        self.assertFalse(self.variant.active)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())
        self.assertTrue(Variant.objects.filter(pk=self.variant.pk).exists())

    def test_owner_stock_adjustment_leaves_history(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("store:owner_stock_adjust_variant", args=[self.variant.pk]),
            {
                "variant": self.variant.pk,
                "operation": "add",
                "quantity": 6,
                "reason": InventoryAdjustment.Reason.RESTOCK,
                "reference": "RECEPCION-TEST",
                "notes": "Prueba de recepción",
            },
        )
        self.assertRedirects(response, reverse("store:owner_stock"))
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 10)
        movement = InventoryAdjustment.objects.get(reference="RECEPCION-TEST")
        self.assertEqual(movement.delta, 6)
        self.assertEqual(movement.created_by, self.owner)

