from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.models import Address

User = get_user_model()

class CustomUserModelTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username='cust', email='customer@test.com', password='password123', role='customer'
        )
        self.pharmacist = User.objects.create_user(
            username='pharm', email='pharmacist@test.com', password='password123', role='pharmacist'
        )
        self.admin = User.objects.create_superuser(
            username='adm', email='admin@test.com', password='password123', role='admin'
        )

    def test_user_roles(self):
        self.assertTrue(self.customer.is_customer())
        self.assertFalse(self.customer.is_pharmacist())
        self.assertTrue(self.pharmacist.is_pharmacist())
        self.assertTrue(self.admin.is_admin_user())

    def test_default_address_switch(self):
        addr1 = Address.objects.create(
            user=self.customer, label='Home', street='123 Main St', city='Rajshahi', district='Rajshahi', is_default=True
        )
        addr2 = Address.objects.create(
            user=self.customer, label='Office', street='456 Tech Park', city='Rajshahi', district='Rajshahi', is_default=True
        )
        addr1.refresh_from_db()
        self.assertFalse(addr1.is_default)
        self.assertTrue(addr2.is_default)

