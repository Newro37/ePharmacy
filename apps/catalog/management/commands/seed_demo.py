"""
Full demo seed command for ePharmacy.
Run: python manage.py seed_demo
Populates: users, addresses, categories, manufacturers,
           medicines, prescriptions, orders, order items, payments.
"""
import uuid
import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from allauth.account.models import EmailAddress
from apps.accounts.models import Address
from apps.catalog.models import Category, Manufacturer, Medicine
from apps.cart.models import Order, OrderItem
from apps.payments.models import Payment
from apps.prescriptions.models import Prescription

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds full demo data: users, medicines, orders, prescriptions, payments.'

    # ------------------------------------------------------------------ #
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n── ePharmacy Demo Seed ──────────────────────────────────'))

        admin      = self._seed_admin()
        pharmacist = self._seed_pharmacist()
        customers  = self._seed_customers()
        cat_map    = self._seed_categories()
        mfg_map    = self._seed_manufacturers()
        medicines  = self._seed_medicines(cat_map, mfg_map)
        self._seed_prescriptions(customers, pharmacist)
        self._seed_orders(customers, medicines)

        self.stdout.write(self.style.SUCCESS('\n✔ Demo data loaded successfully!\n'))
        self.stdout.write('  Login credentials:')
        self.stdout.write('  ┌─────────────────────────────────────────────┐')
        self.stdout.write('  │  Role        │ Email                        │ Password     │')
        self.stdout.write('  │─────────────────────────────────────────────│')
        self.stdout.write('  │  Super Admin │ admin@epharmacy.com          │ admin123     │')
        self.stdout.write('  │  Pharmacist  │ pharmacist@epharmacy.com     │ pharma123    │')
        self.stdout.write('  │  Customer 1  │ tanvir@epharmacy.com         │ customer123  │')
        self.stdout.write('  │  Customer 2  │ riya@epharmacy.com           │ customer123  │')
        self.stdout.write('  │  Customer 3  │ karim@epharmacy.com          │ customer123  │')
        self.stdout.write('  └─────────────────────────────────────────────┘\n')

    # ------------------------------------------------------------------ #
    # Users
    # ------------------------------------------------------------------ #
    def _make_user(self, email, username, first, last, role, phone,
                   is_staff=False, is_superuser=False, password='customer123'):
        user, created = User.objects.get_or_create(
            email=email,
            defaults=dict(username=username, first_name=first, last_name=last,
                          role=role, phone=phone,
                          is_staff=is_staff, is_superuser=is_superuser)
        )
        user.set_password(password)
        user.save()
        EmailAddress.objects.get_or_create(
            user=user, email=email,
            defaults={'verified': True, 'primary': True}
        )
        tag = 'created' if created else 'exists'
        self.stdout.write(f'  User [{tag}] {email}')
        return user

    def _seed_admin(self):
        return self._make_user(
            'admin@epharmacy.com', 'admin',
            'Super', 'Admin', 'admin', '+8801711000001',
            is_staff=True, is_superuser=True, password='admin123'
        )

    def _seed_pharmacist(self):
        ph = self._make_user(
            'pharmacist@epharmacy.com', 'pharmacist',
            'Dr. Rafiqul', 'Islam', 'pharmacist', '+8801711000002',
            is_staff=True, password='pharma123'
        )
        return ph

    def _seed_customers(self):
        customers_data = [
            ('tanvir@epharmacy.com', 'tanvir',   'Tanvir',   'Hossain', '+8801711000003',
             'House 14, Road 5, Kazihata', 'Rajshahi', 'Rajshahi', '6000'),
            ('riya@epharmacy.com',   'riya',     'Riya',     'Sultana', '+8801711000004',
             'Flat 3B, Holding 22, Uposhohor', 'Rajshahi', 'Rajshahi', '6205'),
            ('karim@epharmacy.com',  'karimmd',  'Md. Karim', 'Uddin',  '+8801711000005',
             'Village Baghalia, Boalia', 'Rajshahi', 'Rajshahi', '6100'),
        ]
        users = []
        for email, uname, first, last, phone, street, city, dist, post in customers_data:
            u = self._make_user(email, uname, first, last, 'customer', phone)
            Address.objects.get_or_create(
                user=u, label='Home',
                defaults=dict(street=street, city=city, district=dist,
                              postal_code=post, is_default=True)
            )
            users.append(u)
        return users

    # ------------------------------------------------------------------ #
    # Catalog
    # ------------------------------------------------------------------ #
    def _seed_categories(self):
        data = [
            ('Analgesics & Antipyretics', 'Pain relievers and fever management.'),
            ('Antibiotics',               'Antimicrobial therapies — prescription required.'),
            ('Gastric & Acid Relief',     'Proton pump inhibitors and antacids.'),
            ('Respiratory & Allergy',     'Antihistamines and bronchodilators.'),
            ('Vitamins & Supplements',    'Essential micronutrients and supplements.'),
            ('Cardiovascular & Diabetes', 'Maintenance therapies for BP and glucose.'),
            ('Dermatology',               'Topical and systemic skin treatments.'),
            ('Neurology & Psychiatry',    'CNS active agents — prescription required.'),
        ]
        cat_map = {}
        for name, desc in data:
            c, _ = Category.objects.get_or_create(name=name, defaults={'description': desc})
            cat_map[name] = c
        self.stdout.write(f'  Categories: {len(cat_map)} ready')
        return cat_map

    def _seed_manufacturers(self):
        data = [
            ('Square Pharmaceuticals Ltd.',   'Bangladesh'),
            ('Beximco Pharmaceuticals Ltd.',  'Bangladesh'),
            ('Incepta Pharmaceuticals Ltd.',  'Bangladesh'),
            ('Renata Limited',                'Bangladesh'),
            ('Opsonin Pharma Ltd.',           'Bangladesh'),
            ('ACI Limited',                   'Bangladesh'),
            ('Healthcare Pharmaceuticals',    'Bangladesh'),
        ]
        mfg_map = {}
        for name, country in data:
            m, _ = Manufacturer.objects.get_or_create(name=name, defaults={'country': country})
            mfg_map[name] = m
        self.stdout.write(f'  Manufacturers: {len(mfg_map)} ready')
        return mfg_map

    def _seed_medicines(self, cat_map, mfg_map):
        """Returns list of created Medicine instances."""
        # (name, dosage, category, manufacturer, price, stock, rx, description)
        data = [
            # ── Analgesics ────────────────────────────────────────────────
            ('Napa Extra',    '500mg+65mg',   'Analgesics & Antipyretics',   'Beximco Pharmaceuticals Ltd.',  Decimal('3.50'),   480, False,
             'Paracetamol + Caffeine for rapid relief of headaches and body aches.',
             '2026-12-01'),
            ('Ace Plus',      '500mg+65mg',   'Analgesics & Antipyretics',   'Square Pharmaceuticals Ltd.',   Decimal('3.50'),   320, False,
             'Effective for persistent fever, tension headaches, and muscular soreness.',
             '2027-03-15'),
            ('Ibuprofen',     '400mg',        'Analgesics & Antipyretics',   'ACI Limited',                   Decimal('5.00'),   150, False,
             'NSAID for mild to moderate pain, fever, and inflammation.',
             '2027-06-30'),

            # ── Antibiotics ───────────────────────────────────────────────
            ('Moxacil',       '500mg',        'Antibiotics',                 'Square Pharmaceuticals Ltd.',   Decimal('14.50'),  120, True,
             'Amoxicillin capsule for bacterial respiratory and skin infections.',
             '2026-09-30'),
            ('Azithrocin',    '500mg',        'Antibiotics',                 'Beximco Pharmaceuticals Ltd.',  Decimal('35.00'),   80, True,
             'Macrolide antibiotic for systemic bacterial infections.',
             '2027-01-20'),
            ('Ciprocin 500',  '500mg',        'Antibiotics',                 'Beximco Pharmaceuticals Ltd.',  Decimal('20.00'),   60, True,
             'Ciprofloxacin for urinary tract and enteric infections.',
             '2027-04-10'),

            # ── Gastric ───────────────────────────────────────────────────
            ('Seclo 20',      '20mg',         'Gastric & Acid Relief',       'Square Pharmaceuticals Ltd.',   Decimal('7.00'),   260, False,
             'Omeprazole delayed-release for peptic ulcers and GERD.',
             '2027-08-01'),
            ('Finix 20',      '20mg',         'Gastric & Acid Relief',       'Opsonin Pharma Ltd.',           Decimal('8.00'),   190, False,
             'Rabeprazole for rapid suppression of gastric acid.',
             '2027-05-20'),
            ('Antacid Plus',  'Suspension',   'Gastric & Acid Relief',       'ACI Limited',                   Decimal('45.00'),   75, False,
             'Aluminium hydroxide and magnesium hydroxide antacid suspension.',
             '2026-11-15'),

            # ── Respiratory ───────────────────────────────────────────────
            ('Monas 10',      '10mg',         'Respiratory & Allergy',       'Incepta Pharmaceuticals Ltd.',  Decimal('17.50'),  140, False,
             'Montelukast for asthma management and allergic rhinitis.',
             '2027-07-01'),
            ('Fexo 120',      '120mg',        'Respiratory & Allergy',       'Square Pharmaceuticals Ltd.',   Decimal('10.00'),  170, False,
             'Non-drowsy fexofenadine for allergies and hay fever.',
             '2027-09-15'),
            ('Salbutamol',    '2mg',          'Respiratory & Allergy',       'Healthcare Pharmaceuticals',    Decimal('4.00'),    90, True,
             'Bronchodilator for acute asthma and COPD management.',
             '2026-10-20'),

            # ── Vitamins ──────────────────────────────────────────────────
            ('Bextram Gold',  'Multivitamin', 'Vitamins & Supplements',      'Beximco Pharmaceuticals Ltd.',  Decimal('12.00'),   95, False,
             'Comprehensive multivitamin and mineral formulation.',
             '2027-12-01'),
            ('Ceevit',        '250mg',        'Vitamins & Supplements',      'Square Pharmaceuticals Ltd.',   Decimal('2.00'),   620, False,
             'Vitamin C chewable for immune support.',
             '2028-01-01'),
            ('D-Sol',         '1000IU',       'Vitamins & Supplements',      'Incepta Pharmaceuticals Ltd.',  Decimal('8.00'),   200, False,
             'Vitamin D3 supplement for bone health and immunity.',
             '2027-10-10'),
            ('Zincovit',      '20mg',         'Vitamins & Supplements',      'ACI Limited',                   Decimal('3.00'),   310, False,
             'Zinc supplement for immune function and wound healing.',
             '2027-11-01'),

            # ── Cardiovascular ────────────────────────────────────────────
            ('Osartil 50',    '50mg',         'Cardiovascular & Diabetes',   'Incepta Pharmaceuticals Ltd.',  Decimal('10.00'),  110, True,
             'Losartan for hypertension and cardiovascular risk reduction.',
             '2027-06-01'),
            ('Comprid 80',    '80mg',         'Cardiovascular & Diabetes',   'Renata Limited',                Decimal('16.00'),    8, True,
             'Gliclazide MR for type 2 diabetes. ⚠ Low stock.',
             '2026-08-15'),  # LOW STOCK + near expiry
            ('Atenolol 50',   '50mg',         'Cardiovascular & Diabetes',   'Square Pharmaceuticals Ltd.',   Decimal('6.00'),    5, True,
             'Beta-blocker for hypertension and angina.',
             '2026-07-31'),  # VERY LOW STOCK + expired

            # ── Dermatology ───────────────────────────────────────────────
            ('Betnate-N',     'Cream 15g',    'Dermatology',                 'Square Pharmaceuticals Ltd.',   Decimal('25.00'),   55, False,
             'Betamethasone and neomycin cream for inflammatory skin conditions.',
             '2027-04-01'),
            ('Fungin',        '2% Cream',     'Dermatology',                 'Healthcare Pharmaceuticals',    Decimal('18.00'),   45, False,
             'Clotrimazole antifungal cream for superficial fungal infections.',
             '2027-05-15'),

            # ── Neurology ─────────────────────────────────────────────────
            ('Diazepam',      '5mg',          'Neurology & Psychiatry',      'Opsonin Pharma Ltd.',           Decimal('3.00'),   30, True,
             'Benzodiazepine for anxiety, muscle spasms and seizures.',
             '2027-02-28'),
        ]

        medicines = []
        for row in data:
            name, dosage, cat, mfg, price, stock, rx, desc, expiry = row
            med, created = Medicine.objects.get_or_create(
                name=name,
                defaults=dict(
                    dosage=dosage,
                    category=cat_map[cat],
                    manufacturer=mfg_map[mfg],
                    price=price,
                    stock=stock,
                    prescription_required=rx,
                    description=desc,
                    side_effects='Mild nausea or dizziness may occur. Consult a physician if symptoms persist.',
                    is_active=True,
                    expiry_date=expiry,
                    batch_number=f'BATCH-{name[:4].upper()}-2024',
                )
            )
            medicines.append(med)

        self.stdout.write(f'  Medicines: {len(medicines)} ready ({sum(1 for _,_,_,_,_,s,_,_,_ in data if s <= 10)} low-stock)')
        return medicines

    # ------------------------------------------------------------------ #
    # Prescriptions
    # ------------------------------------------------------------------ #
    def _seed_prescriptions(self, customers, pharmacist):
        """Create prescriptions in various states."""
        # We use a tiny 1×1 white pixel as a placeholder image file.
        import io
        from django.core.files.base import ContentFile

        placeholder = ContentFile(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00'
            b'\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx'
            b'\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00'
            b'\x00IEND\xaeB`\x82',
            name='rx_placeholder.png'
        )

        records = [
            # (customer_index, notes, status, review_notes, days_ago)
            (0, 'Need Moxacil 500mg for throat infection, 7 days course.', 'approved',
             'Verified. 500mg once daily for 7 days approved for dispensation.', 10),
            (0, 'Doctor prescribed Osartil 50mg for blood pressure.',      'approved',
             'Losartan 50mg approved. BP monitoring advised.', 5),
            (0, 'Azithrocin 500mg prescribed by Dr. Rahman.',              'pending',
             '', 1),
            (1, 'Need Ciprocin for UTI diagnosed by clinic.',              'approved',
             'Ciprofloxacin 500mg twice daily for 5 days approved.', 7),
            (1, 'Salbutamol inhaler refill prescription.',                 'rejected',
             'Prescription image unclear. Please resubmit with legible doctor stamp.', 3),
            (1, 'Atenolol 50mg maintenance prescription.',                 'pending',
             '', 2),
            (2, 'Diazepam 5mg for muscle spasm per neurologist advice.',   'approved',
             'Diazepam 5mg approved. Maximum 2 weeks course only.', 6),
            (2, 'Monthly refill: Comprid 80mg for diabetes.',              'pending',
             '', 1),
        ]

        count = 0
        for cust_idx, notes, status, review_notes, days_ago in records:
            customer = customers[cust_idx]

            # Check if this customer+notes combo already exists
            if Prescription.objects.filter(user=customer, notes=notes).exists():
                continue

            rx = Prescription(user=customer, notes=notes, status=status)
            placeholder.seek(0)
            rx.image.save('rx_placeholder.png', ContentFile(placeholder.read()), save=False)
            rx.created_at = timezone.now() - timedelta(days=days_ago)

            if status in ('approved', 'rejected'):
                rx.reviewed_by = pharmacist
                rx.review_notes = review_notes
                rx.reviewed_at = timezone.now() - timedelta(days=days_ago - 1)

            rx.save()
            count += 1

        self.stdout.write(f'  Prescriptions: {count} created')

    # ------------------------------------------------------------------ #
    # Orders
    # ------------------------------------------------------------------ #
    def _seed_orders(self, customers, medicines):
        """Create realistic orders across all statuses with payments."""

        non_rx = [m for m in medicines if not m.prescription_required and m.stock > 0]
        rx     = [m for m in medicines if m.prescription_required and m.stock > 0]

        address_map = {
            0: 'House 14, Road 5, Kazihata, Rajshahi 6000',
            1: 'Flat 3B, Holding 22, Uposhohor, Rajshahi 6205',
            2: 'Village Baghalia, Boalia, Rajshahi 6100',
        }

        # (customer_idx, [(medicine_name, qty)], status, payment_method, days_ago)
        orders_data = [
            # Customer 0 — Tanvir
            (0, [('Napa Extra', 2), ('Seclo 20', 1), ('Ceevit', 3)],
             'delivered', 'card_mock', 25),
            (0, [('Fexo 120', 1), ('Bextram Gold', 1)],
             'delivered', 'cod', 18),
            (0, [('Ibuprofen', 2), ('D-Sol', 1), ('Zincovit', 2)],
             'delivered', 'card_mock', 12),
            (0, [('Monas 10', 1), ('Antacid Plus', 1)],
             'shipped',   'cod', 5),
            (0, [('Ace Plus', 3), ('Finix 20', 1)],
             'processing','card_mock', 3),
            (0, [('Bextram Gold', 2), ('Ceevit', 5)],
             'pending',   'cod', 1),

            # Customer 1 — Riya
            (1, [('Ceevit', 4), ('Zincovit', 2), ('D-Sol', 2)],
             'delivered', 'card_mock', 30),
            (1, [('Fexo 120', 2), ('Monas 10', 1)],
             'delivered', 'cod', 20),
            (1, [('Napa Extra', 5), ('Ibuprofen', 1)],
             'delivered', 'card_mock', 14),
            (1, [('Seclo 20', 2), ('Finix 20', 1), ('Antacid Plus', 1)],
             'shipped',   'cod', 4),
            (1, [('Bextram Gold', 1), ('D-Sol', 1)],
             'pending',   'card_mock', 1),
            (1, [('Ace Plus', 2)],
             'cancelled', 'cod', 8),

            # Customer 2 — Karim
            (2, [('Napa Extra', 3), ('Seclo 20', 2)],
             'delivered', 'cod', 35),
            (2, [('Ibuprofen', 2), ('Ceevit', 6), ('Zincovit', 3)],
             'delivered', 'card_mock', 22),
            (2, [('Fexo 120', 1), ('Bextram Gold', 2)],
             'delivered', 'cod', 15),
            (2, [('Monas 10', 1), ('D-Sol', 2)],
             'processing','card_mock', 2),
            (2, [('Ace Plus', 2), ('Antacid Plus', 1)],
             'pending',   'cod', 1),
        ]

        count = 0
        for cust_idx, items, status, pay_method, days_ago in orders_data:
            customer  = customers[cust_idx]
            med_map   = {m.name: m for m in medicines}

            # Build order items list and total
            line_items = []
            total = Decimal('0.00')
            skip  = False
            for med_name, qty in items:
                med = med_map.get(med_name)
                if not med:
                    skip = True; break
                subtotal = med.price * qty
                total   += subtotal
                line_items.append((med, qty, med.price))
            if skip:
                continue

            # Avoid exact duplicate orders (same customer + total + status)
            if Order.objects.filter(
                user=customer, total_amount=total, status=status
            ).exists():
                continue

            created_at = timezone.now() - timedelta(days=days_ago)

            order = Order.objects.create(
                user=customer,
                status=status,
                total_amount=total,
                delivery_address=address_map[cust_idx],
                created_at=created_at,
            )
            # Force the created_at (auto_now_add ignores assignment by default)
            Order.objects.filter(pk=order.pk).update(created_at=created_at)

            for med, qty, price in line_items:
                OrderItem.objects.create(
                    order=order,
                    medicine=med,
                    medicine_name=med.name,
                    unit_price=price,
                    quantity=qty,
                )

            # Payment
            pay_status = (
                Payment.Status.COMPLETED if status in ('delivered', 'shipped', 'processing')
                else Payment.Status.PENDING if status == 'pending'
                else Payment.Status.FAILED  # cancelled
            )
            if pay_method == 'cod' and status != 'delivered':
                pay_status = Payment.Status.PENDING

            Payment.objects.create(
                order=order,
                amount=total,
                method=pay_method,
                status=pay_status,
                transaction_id=f'TXN-{uuid.uuid4().hex[:8].upper()}',
            )
            count += 1

        self.stdout.write(f'  Orders: {count} created')
