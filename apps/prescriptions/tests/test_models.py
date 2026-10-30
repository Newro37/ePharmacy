from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.prescriptions.models import Prescription

User = get_user_model()

class PrescriptionWorkflowTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username='patient', email='patient@test.com', password='password123'
        )
        self.pharmacist = User.objects.create_user(
            username='doc', email='doc@test.com', password='password123', role='pharmacist'
        )
        fake_file = SimpleUploadedFile('rx.jpg', b'file_content', content_type='image/jpeg')
        self.prescription = Prescription.objects.create(
            user=self.customer, image=fake_file, notes='Need antibiotics'
        )

    def test_initial_status_pending(self):
        self.assertEqual(self.prescription.status, Prescription.Status.PENDING)
        self.assertFalse(self.prescription.is_approved)

    def test_pharmacist_approval_workflow(self):
        self.prescription.status = Prescription.Status.APPROVED
        self.prescription.reviewed_by = self.pharmacist
        self.prescription.review_notes = 'Verified 500mg dose'
        self.prescription.save()

        self.assertTrue(self.prescription.is_approved)
        self.assertEqual(self.prescription.reviewed_by, self.pharmacist)
        # Verify notification signal dispatched
        self.assertEqual(self.customer.notifications.count(), 1)
