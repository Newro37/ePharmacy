from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.catalog.models import Medicine
from apps.cart.models import Cart, CartItem, Order
from apps.accounts.models import Address

User = get_user_model()

class CartViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u1', email='u1@test.com', password='password123')
        self.medicine = Medicine.objects.create(name='Test Med', price=Decimal('20.00'), stock=10)
        self.address = Address.objects.create(user=self.user, label='Home', street='Road 1', city='Rajshahi', district='Rajshahi')
        self.client.login(email='u1@test.com', password='password123')

    def test_add_to_cart_view(self):
        response = self.client.get(reverse('cart:add_to_cart', kwargs={'medicine_id': self.medicine.pk}))
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 1)

    def test_add_to_cart_out_of_stock(self):
        out_of_stock_med = Medicine.objects.create(name='OOS Med', price=Decimal('10.00'), stock=0)
        response = self.client.get(reverse('cart:add_to_cart', kwargs={'medicine_id': out_of_stock_med.pk}))
        self.assertEqual(response.status_code, 302)
        cart, _ = Cart.objects.get_or_create(user=self.user)
        self.assertFalse(cart.items.filter(medicine=out_of_stock_med).exists())

    def test_cart_item_quantity_update(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, medicine=self.medicine, quantity=1)
        # Increase
        self.client.post(reverse('cart:update_cart_item', kwargs={'item_id': item.pk}), {'action': 'increase'})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)
        # Decrease
        self.client.post(reverse('cart:update_cart_item', kwargs={'item_id': item.pk}), {'action': 'decrease'})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

    def test_remove_from_cart(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, medicine=self.medicine, quantity=1)
        self.client.get(reverse('cart:remove_from_cart', kwargs={'item_id': item.pk}))
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_checkout_decrements_stock_and_creates_order(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, medicine=self.medicine, quantity=2)
        response = self.client.post(reverse('cart:checkout'), {
            'address_id': self.address.pk,
            'payment_method': 'cod',
        })
        self.assertEqual(response.status_code, 302)
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock, 8)  # 10 - 2 = 8
        self.assertEqual(Order.objects.filter(user=self.user).count(), 1)
        self.assertEqual(cart.items.count(), 0)  # Cart cleared

