from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from store.models import InventoryAdjustment, Product, StoreLocation, StoreSettings, Variant


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

    def test_effective_price_uses_best_discount_without_stacking(self):
        self.product.discount_percent = Decimal("10")
        self.product.save(update_fields=["discount_percent", "updated_at"])
        self.variant.price = Decimal("1000")
        self.variant.sale_price = Decimal("850")
        self.variant.save(update_fields=["price", "sale_price", "updated_at"])
        settings_obj = StoreSettings.get_solo()
        settings_obj.promotion_active = True
        settings_obj.global_discount_percent = Decimal("20")
        settings_obj.save()
        self.assertEqual(self.variant.current_price, Decimal("800.00"))

        settings_obj.promotion_active = False
        settings_obj.save()
        self.assertEqual(self.variant.current_price, Decimal("850"))

    def test_owner_can_manage_pickup_location_with_full_address(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("store:owner_location_create"),
            {
                "name": "Orizaba — Centro / La Concordia",
                "street_address": "Oriente 5 esquina con Norte 28 #1500",
                "neighborhood": "Centro / La Concordia",
                "city": "Orizaba",
                "state": "Veracruz",
                "postal_code": "94300",
                "country_code": "MX",
                "contact_name": "Agave Racquet Club",
                "contact_email": "agaveracquetclub@gmail.com",
                "phone": "2720000000",
                "opening_hours": "Con cita",
                "pickup_enabled": "on",
                "active": "on",
            },
        )
        self.assertRedirects(response, reverse("store:owner_locations"))
        location = StoreLocation.objects.get(name__startswith="Orizaba")
        self.assertIn("Oriente 5", location.full_address)
        self.assertIn("94300", location.full_address)

