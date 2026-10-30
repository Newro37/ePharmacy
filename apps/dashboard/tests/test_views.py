from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class DashboardAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='adm2', email='admin2@test.com', password='password123', role='admin'
        )
        self.customer = User.objects.create_user(
            username='cust2', email='cust2@test.com', password='password123', role='customer'
        )

    def test_customer_cannot_access_admin_dashboard(self):
        self.client.login(email='cust2@test.com', password='password123')
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirects away to catalog:home

    def test_admin_can_access_dashboard(self):
        self.client.login(email='admin2@test.com', password='password123')
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 200)