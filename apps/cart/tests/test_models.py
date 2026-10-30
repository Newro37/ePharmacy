from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.catalog.models import Medicine
from apps.cart.models import Cart, CartItem, Order, OrderItem

User = get_user_model()

class CartAndOrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='buyer', email='buyer@test.com', password='password123'
        )
        self.medicine = Medicine.objects.create(
            name='Paracetamol', price=Decimal('10.00'), stock=50
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart, medicine=self.medicine, quantity=3
        )

    def test_cart_item_subtotal(self):
        self.assertEqual(self.cart_item.get_subtotal(), Decimal('30.00'))

    def test_cart_total_and_count(self):
        self.assertEqual(self.cart.get_total(), Decimal('30.00'))
        self.assertEqual(self.cart.get_item_count(), 3)

    @patch('apps.cart.signals.send_mail')
    def test_order_creation_and_observer_signal(self, mock_mail):
        order = Order.objects.create(
            user=self.user, total_amount=Decimal('30.00'), delivery_address='Test Address'
        )
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertTrue(order.can_cancel())
        # Observer pattern signal fired
        self.assertTrue(mock_mail.called)
        self.assertEqual(self.user.notifications.count(), 1)

    def test_order_cancellation_constraint(self):
        order = Order.objects.create(
            user=self.user, total_amount=Decimal('30.00'), delivery_address='Test Address',
            status=Order.Status.SHIPPED
        )
        self.assertFalse(order.can_cancel())
