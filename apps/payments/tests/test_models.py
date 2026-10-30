from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.cart.models import Order
from apps.payments.models import Payment, MockPaymentStrategy, PaymentContext

User = get_user_model()

class PaymentStrategyPatternTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='payee', email='payee@test.com', password='password123')
        self.order = Order.objects.create(user=self.user, total_amount=Decimal('500.00'), delivery_address='Test Road')
        self.payment = Payment.objects.create(order=self.order, amount=Decimal('500.00'), method=Payment.Method.CARD_MOCK)

    def test_mock_payment_strategy_execution(self):
        strategy = MockPaymentStrategy()
        context = PaymentContext(strategy)
        success = context.execute_payment(self.payment)

        self.assertTrue(success)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.COMPLETED)
        self.assertTrue(self.payment.transaction_id.startswith('TXN-MOCK-'))

    def test_cod_payment_strategy_execution(self):
        self.payment.method = Payment.Method.COD
        strategy = MockPaymentStrategy()
        context = PaymentContext(strategy)
        success = context.execute_payment(self.payment)

        self.assertTrue(success)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PENDING)
        self.assertTrue(self.payment.transaction_id.startswith('COD-'))

