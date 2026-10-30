from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification, NotificationFactory

User = get_user_model()

class NotificationFactoryPatternTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='notify_user', email='notify@test.com', password='password123')

    def test_factory_method_creation(self):
        notif = NotificationFactory.create_order_notification(
            user=self.user,
            order=type('FakeOrder', (), {'pk': 99, 'get_status_display': lambda self: 'Processing'})()
        )
        self.assertEqual(notif.user, self.user)
        self.assertEqual(notif.notification_type, Notification.Type.ORDER_UPDATE)
        self.assertEqual(notif.link, '/cart/order/99/')
        self.assertFalse(notif.is_read)
