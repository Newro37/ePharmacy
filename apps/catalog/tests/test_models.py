from django.test import TestCase
from decimal import Decimal
from apps.catalog.models import Category, Manufacturer, Medicine

class MedicineModelAndRepositoryTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Analgesics')
        self.manufacturer = Manufacturer.objects.create(name='Square Pharmaceuticals')
        self.med1 = Medicine.objects.create(
            name='Napa Extra', dosage='500mg', price=Decimal('2.50'), stock=100,
            category=self.category, manufacturer=self.manufacturer
        )
        self.med2 = Medicine.objects.create(
            name='Ace Plus', dosage='500mg', price=Decimal('3.00'), stock=0,
            category=self.category, manufacturer=self.manufacturer
        )
        self.med3 = Medicine.objects.create(
            name='Moxacil', dosage='500mg', price=Decimal('15.00'), stock=5,
            category=self.category, manufacturer=self.manufacturer, prescription_required=True
        )

    def test_repository_available(self):
        available = Medicine.objects.available()
        self.assertIn(self.med1, available)
        self.assertNotIn(self.med2, available)

    def test_repository_low_stock(self):
        low = Medicine.objects.low_stock(threshold=10)
        self.assertIn(self.med3, low)
        self.assertNotIn(self.med1, low)

    def test_repository_search(self):
        res = Medicine.objects.search('Napa')
        self.assertIn(self.med1, res)
        self.assertNotIn(self.med3, res)

    def test_in_stock_property(self):
        self.assertTrue(self.med1.is_in_stock)
        self.assertFalse(self.med2.is_in_stock)


    def test_is_low_stock_property(self):
        self.assertFalse(self.med1.is_low_stock)
        self.assertFalse(self.med2.is_low_stock)
        self.assertTrue(self.med3.is_low_stock)
