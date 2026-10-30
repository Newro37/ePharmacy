import abc
import uuid
from decimal import Decimal
from django.db import models
from apps.cart.models import Order

class Payment(models.Model):
    class Method(models.TextChoices):
        COD = 'cod', 'Cash on Delivery'
        CARD_MOCK = 'card_mock', 'Online Card / Mobile Banking'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.COD)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment #{self.pk} for Order #{self.order.pk} [{self.status}]"

class PaymentStrategy(abc.ABC):
    """Strategy Pattern: Abstract strategy interface."""
    @abc.abstractmethod
    def process(self, payment: Payment) -> bool:
        pass

class MockPaymentStrategy(PaymentStrategy):
    """Concrete Strategy: Simulates instant payment completion."""
    def process(self, payment: Payment) -> bool:
        if payment.method == Payment.Method.COD:
            payment.status = Payment.Status.PENDING
            payment.transaction_id = f"COD-{uuid.uuid4().hex[:8].upper()}"
        else:
            payment.status = Payment.Status.COMPLETED
            payment.transaction_id = f"TXN-MOCK-{uuid.uuid4().hex[:8].upper()}"
        payment.save()
        return True

class PaymentContext:
    """Strategy Pattern: Context class holding a reference to concrete strategy."""
    def __init__(self, strategy: PaymentStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: PaymentStrategy):
        self._strategy = strategy

    def execute_payment(self, payment: Payment) -> bool:
        return self._strategy.process(payment)

