from django.db import models
from django.conf import settings

class Notification(models.Model):
    class Type(models.TextChoices):
        ORDER_UPDATE = 'order_update', 'Order Update'
        PRESCRIPTION_UPDATE = 'prescription_update', 'Prescription Update'
        STOCK_ALERT = 'stock_alert', 'Stock Alert'
        SYSTEM = 'system', 'System Message'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=30, choices=Type.choices, default=Type.SYSTEM)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} for {self.user.email}"

class NotificationFactory:
    """Factory Method Pattern: Encapsulates creation of polymorphic notifications."""
    @staticmethod
    def create_order_notification(user, order, message=None):
        msg = message or f"Your order #{order.pk} status updated to {order.get_status_display()}."
        return Notification.objects.create(
            user=user,
            notification_type=Notification.Type.ORDER_UPDATE,
            title=f"Order #{order.pk} Update",
            message=msg,
            link=f"/cart/order/{order.pk}/"
        )

    @staticmethod
    def create_prescription_notification(user, prescription, message=None):
        msg = message or f"Your prescription #{prescription.pk} is now {prescription.get_status_display()}."
        return Notification.objects.create(
            user=user,
            notification_type=Notification.Type.PRESCRIPTION_UPDATE,
            title="Prescription Review Complete",
            message=msg,
            link="/prescriptions/my/"
        )

    @staticmethod
    def create_low_stock_alert(user, medicine):
        return Notification.objects.create(
            user=user,
            notification_type=Notification.Type.STOCK_ALERT,
            title=f"Low Stock Alert: {medicine.name}",
            message=f"{medicine.name} has reached a low stock level of {medicine.stock} units.",
            link=f"/dashboard/medicines/"
        )

