from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.accounts.models import Address

User = get_user_model()

class AccountViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u_prof', email='u_prof@test.com', password='password123')
        self.client.login(email='u_prof@test.com', password='password123')

    def test_profile_view_render_and_update(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

        post_res = self.client.post(reverse('accounts:profile'), {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'phone': '+8801700000000',
        })
        self.assertEqual(post_res.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'UpdatedFirst')

    def test_address_create_and_delete(self):
        create_res = self.client.post(reverse('accounts:address_add'), {
            'label': 'Office',
            'street': 'Level 4, IT Park',
            'city': 'Rajshahi',
            'district': 'Rajshahi',
            'postal_code': '6000',
            'is_default': True,
        })
        self.assertEqual(create_res.status_code, 302)
        address = Address.objects.filter(user=self.user).first()
        self.assertIsNotNone(address)
        self.assertEqual(address.label, 'Office')

        del_res = self.client.post(reverse('accounts:address_delete', kwargs={'pk': address.pk}))
        self.assertEqual(del_res.status_code, 302)
        self.assertFalse(Address.objects.filter(pk=address.pk).exists())

