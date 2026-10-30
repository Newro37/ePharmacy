from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Sum
from apps.catalog.models import Medicine, Category, Manufacturer
from apps.cart.models import Order
from apps.prescriptions.models import Prescription
from .forms import MedicineForm

User = get_user_model()

def staff_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_pharmacist() or request.user.is_admin_user()):
            messages.error(request, "Access restricted to authorized pharmacy staff.")
            return redirect('catalog:home')
        return view_func(request, *args, **kwargs)
    return wrapper

@staff_required
def dashboard_home_view(request):
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status=Order.Status.PENDING).count()
    gross_revenue = Order.objects.exclude(status=Order.Status.CANCELLED).aggregate(total=Sum('total_amount'))['total'] or 0
    low_stock_medicines = Medicine.objects.low_stock(threshold=10)
    pending_prescriptions = Prescription.objects.filter(status=Prescription.Status.PENDING).count()
    recent_orders = Order.objects.all().order_by('-created_at')[:8]

    return render(request, 'dashboard/home.html', {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'gross_revenue': gross_revenue,
        'low_stock_count': low_stock_medicines.count(),
        'low_stock_medicines': low_stock_medicines[:5],
        'pending_prescriptions': pending_prescriptions,
        'recent_orders': recent_orders,
    })

@staff_required
def medicine_list_view(request):
    medicines = Medicine.objects.all().order_by('name')
    return render(request, 'dashboard/medicine_list.html', {'medicines': medicines})

@staff_required
def medicine_create_view(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES)
        if form.is_valid():
            medicine = form.save()
            messages.success(request, f"Added {medicine.name} to pharmacy inventory.")
            return redirect('dashboard:medicine_list')
    else:
        form = MedicineForm()
    return render(request, 'dashboard/medicine_form.html', {'form': form, 'title': 'Add New Medicine'})

@staff_required
def medicine_update_view(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated {medicine.name}.")
            return redirect('dashboard:medicine_list')
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'dashboard/medicine_form.html', {'form': form, 'title': f'Edit {medicine.name}'})

@staff_required
def medicine_toggle_active_view(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    medicine.is_active = not medicine.is_active
    medicine.save()
    status_str = "activated" if medicine.is_active else "deactivated"
    messages.info(request, f"{medicine.name} has been {status_str}.")
    return redirect('dashboard:medicine_list')

@staff_required
def order_pipeline_view(request):
    orders = Order.objects.all().order_by('-created_at')
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'dashboard/orders.html', {
        'orders': orders,
        'status_choices': Order.Status.choices,
        'current_status': status_filter,
    })

@staff_required
def order_status_update_view(request, pk):
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get('status')
        if new_status in Order.Status.values:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.pk} status updated to {order.get_status_display()}.")
    return redirect('dashboard:orders')

@staff_required
def user_management_view(request):
    if not request.user.is_admin_user():
        messages.error(request, "Access restricted to Super Admin.")
        return redirect('dashboard:home')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'dashboard/users.html', {'users': users})
