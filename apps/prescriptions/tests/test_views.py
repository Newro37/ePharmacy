from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.prescriptions.models import Prescription

User = get_user_model()

class PrescriptionViewTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='cust3', email='cust3@test.com', password='password123')
        self.pharmacist = User.objects.create_user(username='pharma3', email='pharma3@test.com', password='password123', role='pharmacist')
        self.fake_image = SimpleUploadedFile('rx.jpg', b'image_bits', content_type='image/jpeg')

    def test_customer_can_upload_prescription(self):
        self.client.login(email='cust3@test.com', password='password123')
        response = self.client.post(reverse('prescriptions:upload'), {
            'image': self.fake_image,
            'notes': 'Doctor advised 1 tablet daily',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Prescription.objects.filter(user=self.customer).count(), 1)

    def test_customer_cannot_access_review_queue(self):
        self.client.login(email='cust3@test.com', password='password123')
        response = self.client.get(reverse('prescriptions:review_list'))
        self.assertEqual(response.status_code, 302)  # Denied and redirected

    def test_pharmacist_can_access_queue_and_approve(self):
        rx = Prescription.objects.create(user=self.customer, image=self.fake_image, notes='Need antibiotics')
        self.client.login(email='pharma3@test.com', password='password123')
        
        # Access queue
        response = self.client.get(reverse('prescriptions:review_list'))
        self.assertEqual(response.status_code, 200)

        # Approve Rx
        response = self.client.post(reverse('prescriptions:review_detail', kwargs={'pk': rx.pk}), {
            'action': 'approve',
            'review_notes': 'Approved 500mg dose for 7 days',
        })
        self.assertEqual(response.status_code, 302)
        rx.refresh_from_db()
        self.assertEqual(rx.status, Prescription.Status.APPROVED)
        self.assertEqual(rx.reviewed_by, self.pharmacist)
