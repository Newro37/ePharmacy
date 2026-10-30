from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Prescription

@login_required
def upload_prescription_view(request):
    if request.method == 'POST' and request.FILES.get('image'):
        prescription = Prescription.objects.create(
            user=request.user,
            image=request.FILES['image'],
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f"Prescription #{prescription.pk} uploaded successfully! Our pharmacist will review it promptly.")
        return redirect('prescriptions:my_prescriptions')
    return render(request, 'prescriptions/upload.html')

@login_required
def my_prescriptions_view(request):
    prescriptions = request.user.prescriptions.all().order_by('-created_at')
    return render(request, 'prescriptions/my_prescriptions.html', {'prescriptions': prescriptions})

@login_required
def prescription_detail_view(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk, user=request.user)
    return render(request, 'prescriptions/detail.html', {'prescription': prescription})

@login_required
def review_list_view(request):
    if not (request.user.is_pharmacist() or request.user.is_admin_user()):
        messages.error(request, "Access restricted to licensed clinical pharmacists.")
        return redirect('catalog:home')
    pending_list = Prescription.objects.filter(status=Prescription.Status.PENDING).order_by('created_at')
    reviewed_list = Prescription.objects.exclude(status=Prescription.Status.PENDING).order_by('-reviewed_at')[:20]
    return render(request, 'prescriptions/review_list.html', {
        'pending_list': pending_list,
        'reviewed_list': reviewed_list,
    })

@login_required
def review_detail_view(request, pk):
    if not (request.user.is_pharmacist() or request.user.is_admin_user()):
        messages.error(request, "Access restricted to licensed clinical pharmacists.")
        return redirect('catalog:home')
    prescription = get_object_or_404(Prescription, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        review_notes = request.POST.get('review_notes', '').strip()
        if action == 'approve':
            prescription.status = Prescription.Status.APPROVED
            prescription.reviewed_by = request.user
            prescription.review_notes = review_notes or 'Approved for dispensation.'
            prescription.reviewed_at = timezone.now()
            prescription.save()
            messages.success(request, f"Prescription #{prescription.pk} approved.")
            return redirect('prescriptions:review_list')
        elif action == 'reject':
            prescription.status = Prescription.Status.REJECTED
            prescription.reviewed_by = request.user
            prescription.review_notes = review_notes or 'Rejected due to clinical safety concerns.'
            prescription.reviewed_at = timezone.now()
            prescription.save()
            messages.warning(request, f"Prescription #{prescription.pk} rejected.")
            return redirect('prescriptions:review_list')

    return render(request, 'prescriptions/review.html', {'prescription': prescription})

