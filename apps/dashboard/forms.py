from django import forms
from django.contrib.auth import get_user_model
from apps.catalog.models import Medicine

User = get_user_model()

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = [
            'name', 'category', 'manufacturer', 'dosage', 'price', 'stock',
            'batch_number', 'expiry_date',
            'prescription_required', 'description', 'side_effects', 'image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.Select(attrs={'class': 'form-select'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 500mg, 10ml'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BATCH-2026-X'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'prescription_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'side_effects': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class StaffCreationForm(forms.Form):
    """Super Admin form to register licensed Pharmacist staff accounts."""
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'pharmacist@epharmacy.com'}))
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+88017...'}))
    role = forms.ChoiceField(
        choices=[('pharmacist', 'Licensed Clinical Pharmacist'), ('admin', 'System Super Admin')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Set initial password'}))
