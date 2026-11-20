from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from store.models import InventoryAdjustment, Order, Payment, Product, Variant
from store.services.inventory import (
    OrderLineRequest,
    approve_order_payment,
    create_order_with_stock_hold,
    release_order_stock,
)


@override_settings(STOCK_HOLD_MINUTES=15)
class InventoryFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("cliente", "cliente@example.com", "secure-test-password")
        self.product = Product.objects.create(
            name="Raqueta de prueba", slug="raqueta-prueba", brand="Agave / Genérica",
            category="Raquetas de tenis", show_in_catalog=True,
        )
        self.variant = Variant.objects.create(
            product=self.product, sku="TEST-001", name="Única", price=Decimal("1000.00"), stock=1,
        )

    def make_order(self):
        return create_order_with_stock_hold(
            lines=[OrderLineRequest(self.variant.id, 1)],
            user=self.user,
            customer_name="Cliente Prueba",
            customer_email="cliente@example.com",
            customer_phone="2220000000",
            fulfillment=Order.Fulfillment.PICKUP,
        )

    def test_last_unit_cannot_be_sold_twice(self):
        first = self.make_order()
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 0)
        with self.assertRaises(ValidationError):
            self.make_order()
        self.assertEqual(first.items.get().quantity, 1)

    def test_expired_order_releases_stock_once(self):
        order = self.make_order()
        release_order_stock(order, status=Order.Status.EXPIRED)
        release_order_stock(order, status=Order.Status.EXPIRED)
        self.variant.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.variant.stock, 1)
        self.assertTrue(order.stock_released)
        self.assertEqual(InventoryAdjustment.objects.filter(reference=order.number, delta=1).count(), 1)

    def test_approved_payment_keeps_stock_decremented(self):
        order = self.make_order()
        payment = Payment.objects.create(
            order=order, provider=Payment.Provider.MANUAL, method=Payment.Method.TRANSFER,
            amount=order.total,
        )
        approve_order_payment(order, payment=payment)
        order.refresh_from_db()
        payment.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(payment.status, Payment.Status.APPROVED)
        self.assertEqual(self.variant.stock, 0)

