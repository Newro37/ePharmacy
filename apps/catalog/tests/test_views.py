from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.catalog.models import Category, Medicine

class CatalogViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Vitamins')
        self.medicine = Medicine.objects.create(
            name='Vitamin C Chewable', price=Decimal('5.00'), stock=100, category=self.category
        )

    def test_home_page_view(self):
        response = self.client.get(reverse('catalog:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vitamin C Chewable')

    def test_catalog_list_and_search(self):
        response = self.client.get(reverse('catalog:medicine_list'), {'q': 'Vitamin'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vitamin C Chewable')

    def test_catalog_category_filter(self):
        response = self.client.get(reverse('catalog:medicine_list'), {'category': self.category.slug})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vitamin C Chewable')

    def test_medicine_detail_view(self):
        response = self.client.get(reverse('catalog:medicine_detail', kwargs={'slug': self.medicine.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vitamin C Chewable')

