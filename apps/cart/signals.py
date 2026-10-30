from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Order
from apps.notifications.models import NotificationFactory

@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    """Observer Pattern: Order state changes notify user and trigger email."""
    if created:
        NotificationFactory.create_order_notification(
            user=instance.user,
            order=instance,
            message=f"Order #{instance.pk} has been placed successfully."
        )
        try:
            send_mail(
                subject=f"Order #{instance.pk} Confirmation",
                message=f"Thank you for ordering. Your order #{instance.pk} total is ৳{instance.total_amount}.",
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@epharmacy.com',
                recipient_list=[instance.user.email],
                fail_silently=True,
            )
        except Exception:
            pass
    else:
        NotificationFactory.create_order_notification(
            user=instance.user,
            order=instance,
            message=f"Order #{instance.pk} status updated to {instance.get_status_display()}."
        )
