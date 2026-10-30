from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Prescription
from apps.notifications.models import NotificationFactory

@receiver(post_save, sender=Prescription)
def prescription_status_changed(sender, instance, created, **kwargs):
    """Observer Pattern: Triggers notification when prescription review is completed."""
    if not created and instance.status in [Prescription.Status.APPROVED, Prescription.Status.REJECTED]:
        msg = f"Your prescription #{instance.pk} has been {instance.get_status_display()} by our clinical pharmacist."
        if instance.review_notes:
            msg += f" Remarks: {instance.review_notes}"
        NotificationFactory.create_prescription_notification(
            user=instance.user,
            prescription=instance,
            message=msg
        )

