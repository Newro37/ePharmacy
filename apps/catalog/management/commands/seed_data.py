from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from apps.accounts.models import Address
from apps.catalog.models import Category, Manufacturer, Medicine

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds initial demonstration data for ePharmacy (Single-Pharmacy Enterprise)'

    def handle(self, *args, **options):
        self.stdout.write("Seeding ePharmacy database...")

        # 1. Seed Users
        admin_user, _ = User.objects.get_or_create(
            email='admin@epharmacy.com',
            defaults={
                'username': 'admin',
                'first_name': 'Super',
                'last_name': 'Admin',
                'role': 'admin',
                'phone': '+8801711000001',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()
        EmailAddress.objects.get_or_create(user=admin_user, email=admin_user.email, defaults={'verified': True, 'primary': True})

        pharmacist_user, _ = User.objects.get_or_create(
            email='pharmacist@epharmacy.com',
            defaults={
                'username': 'pharmacist',
                'first_name': 'Dr. Rafiqul',
                'last_name': 'Islam',
                'role': 'pharmacist',
                'phone': '+8801711000002',
                'is_staff': True,
            }
        )
        pharmacist_user.set_password('pharma123')
        pharmacist_user.save()
        EmailAddress.objects.get_or_create(user=pharmacist_user, email=pharmacist_user.email, defaults={'verified': True, 'primary': True})

        customer_user, _ = User.objects.get_or_create(
            email='customer@epharmacy.com',
            defaults={
                'username': 'customer',
                'first_name': 'Tanvir',
                'last_name': 'Hossain',
                'role': 'customer',
                'phone': '+8801711000003',
            }
        )
        customer_user.set_password('customer123')
        customer_user.save()
        EmailAddress.objects.get_or_create(user=customer_user, email=customer_user.email, defaults={'verified': True, 'primary': True})

        Address.objects.get_or_create(
            user=customer_user,
            label='Home',
            defaults={
                'street': 'House 14, Road 5, Kazihata',
                'city': 'Rajshahi',
                'district': 'Rajshahi',
                'postal_code': '6000',
                'is_default': True,
            }
        )

        # 2. Seed Categories
        categories_data = [
            ('Analgesics & Antipyretics', 'Pain relievers and fever management medications.'),
            ('Antibiotics', 'Antimicrobial therapies requiring strict physician prescription.'),
            ('Gastric & Acid Relief', 'Proton pump inhibitors and antacids.'),
            ('Respiratory & Allergy', 'Antihistamines and bronchodilators.'),
            ('Vitamins & Supplements', 'Essential micronutrients and dietary supplements.'),
            ('Cardiovascular & Diabetes', 'Maintenance therapies for blood pressure and glucose.'),
        ]
        cat_map = {}
        for name, desc in categories_data:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'description': desc})
            cat_map[name] = cat

        # 3. Seed Manufacturers
        mfg_data = [
            ('Square Pharmaceuticals Ltd.', 'Bangladesh', 'https://www.squarepharma.com.bd'),
            ('Beximco Pharmaceuticals Ltd.', 'Bangladesh', 'https://www.beximcopharma.com'),
            ('Incepta Pharmaceuticals Ltd.', 'Bangladesh', 'https://www.inceptapharma.com'),
            ('Renata Limited', 'Bangladesh', 'https://www.renata-ltd.com'),
            ('Opsonin Pharma Ltd.', 'Bangladesh', 'https://www.opsonin.com'),
        ]
        mfg_map = {}
        for name, country, site in mfg_data:
            mfg, _ = Manufacturer.objects.get_or_create(name=name, defaults={'country': country, 'website': site})
            mfg_map[name] = mfg

        # 4. Seed Medicines
        medicines_data = [
            # Name, Dosage, Category, Manufacturer, Price, Stock, Rx Required, Desc
            ('Napa Extra', '500mg+65mg', 'Analgesics & Antipyretics', 'Beximco Pharmaceuticals Ltd.', Decimal('3.50'), 450, False,
             'Paracetamol and Caffeine formulation for rapid relief from severe headaches and body aches.'),
            ('Ace Plus', '500mg+65mg', 'Analgesics & Antipyretics', 'Square Pharmaceuticals Ltd.', Decimal('3.50'), 300, False,
             'Effective treatment for persistent fever, tension headaches, and muscular soreness.'),
            ('Moxacil', '500mg', 'Antibiotics', 'Square Pharmaceuticals Ltd.', Decimal('14.50'), 120, True,
             'Amoxicillin capsule for bacterial infections of respiratory tract and skin. Requires prescription.'),
            ('Azithrocin', '500mg', 'Antibiotics', 'Beximco Pharmaceuticals Ltd.', Decimal('35.00'), 80, True,
             'Broad-spectrum macrolide antibiotic for systemic bacterial infections. Prescription mandatory.'),
            ('Seclo 20', '20mg', 'Gastric & Acid Relief', 'Square Pharmaceuticals Ltd.', Decimal('7.00'), 250, False,
             'Omeprazole delayed-release capsule for peptic ulcers, heartburn, and GERD.'),
            ('Finix 20', '20mg', 'Gastric & Acid Relief', 'Opsonin Pharma Ltd.', Decimal('8.00'), 180, False,
             'Rabeprazole sodium tablet for rapid suppression of gastric acid secretion.'),
            ('Monas 10', '10mg', 'Respiratory & Allergy', 'Incepta Pharmaceuticals Ltd.', Decimal('17.50'), 140, False,
             'Montelukast sodium chewable tablet for chronic asthma management and seasonal allergic rhinitis.'),
            ('Fexo 120', '120mg', 'Respiratory & Allergy', 'Square Pharmaceuticals Ltd.', Decimal('10.00'), 160, False,
             'Non-drowsy fexofenadine hydrochloride antihistamine for allergies and hay fever.'),
            ('Bextram Gold', 'Multivitamin', 'Vitamins & Supplements', 'Beximco Pharmaceuticals Ltd.', Decimal('12.00'), 95, False,
             'Comprehensive daily multivitamin and mineral formulation with antioxidant properties.'),
            ('Ceevit', '250mg', 'Vitamins & Supplements', 'Square Pharmaceuticals Ltd.', Decimal('2.00'), 600, False,
             'Ascorbic acid Vitamin C chewable tablet for immune support and scurvy prevention.'),
            ('Osartil 50', '50mg', 'Cardiovascular & Diabetes', 'Incepta Pharmaceuticals Ltd.', Decimal('10.00'), 110, True,
             'Losartan potassium tablet for hypertension control and cardiovascular risk reduction.'),
            ('Comprid 80', '80mg', 'Cardiovascular & Diabetes', 'Renata Limited', Decimal('16.00'), 8, True,
             'Gliclazide modified-release tablet for type 2 diabetes management. Note: Low Stock warning!'),
        ]

        for name, dosage, cat_name, mfg_name, price, stock, rx, desc in medicines_data:
            Medicine.objects.get_or_create(
                name=name,
                defaults={
                    'dosage': dosage,
                    'category': cat_map[cat_name],
                    'manufacturer': mfg_map[mfg_name],
                    'price': price,
                    'stock': stock,
                    'prescription_required': rx,
                    'description': desc,
                    'side_effects': 'Mild nausea, headache, or dizziness may occur. Consult physician if symptoms persist.',
                    'is_active': True,
                }
            )

        self.stdout.write(self.style.SUCCESS("Database successfully seeded with 3 roles, categories, and 12 authentic medicines!"))

