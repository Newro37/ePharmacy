from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Sum, Avg, Count
from allauth.account.models import EmailAddress
from apps.catalog.models import Medicine, Category, Manufacturer
from apps.cart.models import Order
from apps.payments.models import Payment
from apps.prescriptions.models import Prescription
from .forms import MedicineForm, StaffCreationForm

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
    """(Super Admin & Pharmacist): View Financial & Revenue Telemetry."""
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status=Order.Status.PENDING).count()
    settled_orders = Order.objects.exclude(status=Order.Status.CANCELLED)
    
    # Financial Telemetry KPIs
    gross_revenue = settled_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    avg_order_value = settled_orders.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')
    
    # Revenue Breakdown by Payment Method
    cod_revenue = Payment.objects.filter(method=Payment.Method.COD, status=Payment.Status.COMPLETED).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    online_revenue = Payment.objects.filter(method=Payment.Method.CARD_MOCK, status=Payment.Status.COMPLETED).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    low_stock_medicines = Medicine.objects.low_stock(threshold=10)
    pending_prescriptions = Prescription.objects.filter(status=Prescription.Status.PENDING).count()
    recent_orders = Order.objects.all().order_by('-created_at')[:8]

    return render(request, 'dashboard/home.html', {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'gross_revenue': gross_revenue,
        'avg_order_value': avg_order_value,
        'cod_revenue': cod_revenue,
        'online_revenue': online_revenue,
        'low_stock_count': low_stock_medicines.count(),
        'low_stock_medicines': low_stock_medicines[:6],
        'pending_prescriptions': pending_prescriptions,
        'recent_orders': recent_orders,
    })

@staff_required
def medicine_list_view(request):
    """(Pharmacist & Admin): Update Medicine Stock, Batches & Expiry Dates / Catalog CRUD."""
    medicines = Medicine.objects.all().order_by('name')
    return render(request, 'dashboard/medicine_list.html', {'medicines': medicines})

@staff_required
def medicine_create_view(request):
    """(Super Admin): Manage Catalog & Pricing CRUD - Add Product."""
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES)
        if form.is_valid():
            medicine = form.save()
            messages.success(request, f"Added {medicine.name} to pharmacy catalog & inventory.")
            return redirect('dashboard:medicine_list')
    else:
        form = MedicineForm()
    return render(request, 'dashboard/medicine_form.html', {'form': form, 'title': 'Add New Medicine & Set Pricing'})

@staff_required
def medicine_update_view(request, pk):
    """(Super Admin & Pharmacist): Update Medicine Stock & Batches & Pricing."""
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated {medicine.name} inventory, batch, and pricing.")
            return redirect('dashboard:medicine_list')
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'dashboard/medicine_form.html', {'form': form, 'title': f'Edit & Update {medicine.name}'})

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
    """(Pharmacist & Admin): Fulfill & Dispatch Orders Pipeline."""
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
    """(Pharmacist & Admin): Update order status directly."""
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get('status')
        if new_status in Order.Status.values:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.pk} status updated to {order.get_status_display()}.")
    return redirect('dashboard:orders')

@staff_required
def order_fulfill_view(request, pk):
    """(Pharmacist): Step 2 - Fulfill order (verifies Rx packaging, transitions to Processing)."""
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        order.status = Order.Status.PROCESSING
        order.save()
        messages.success(request, f"Order #{order.pk} marked as FULFILLED & IN PROCESSING.")
    return redirect('dashboard:orders')

@staff_required
def order_dispatch_view(request, pk):
    """(Pharmacist): Step 3 - Dispatch order to courier logistics."""
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        order.status = Order.Status.SHIPPED
        order.save()
        messages.success(request, f"Order #{order.pk} DISPATCHED with courier delivery.")
    return redirect('dashboard:orders')

@staff_required
def order_deliver_view(request, pk):
    """(Pharmacist & Admin): Step 4 - Mark as Delivered."""
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        order.status = Order.Status.DELIVERED
        order.save()
        messages.success(request, f"Order #{order.pk} successfully DELIVERED to patient.")
    return redirect('dashboard:orders')

@staff_required
def user_management_view(request):
    """(Super Admin): Staff Management (Pharmacists) and Customer Accounts."""
    if not request.user.is_admin_user():
        messages.error(request, "Access restricted to Super Admin.")
        return redirect('dashboard:home')
    users = User.objects.all().order_by('-date_joined')
    pharmacist_count = users.filter(role=User.Role.PHARMACIST).count()
    customer_count = users.filter(role=User.Role.CUSTOMER).count()
    return render(request, 'dashboard/users.html', {
        'users': users,
        'pharmacist_count': pharmacist_count,
        'customer_count': customer_count,
    })

@staff_required
def staff_create_view(request):
    """(Super Admin): Register a new licensed Pharmacist staff account."""
    if not request.user.is_admin_user():
        messages.error(request, "Access restricted to Super Admin.")
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                messages.error(request, "An account with this email address already exists.")
            else:
                user = User.objects.create_user(
                    username=email.split('@')[0],
                    email=email,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    phone=form.cleaned_data['phone'],
                    role=form.cleaned_data['role'],
                    is_staff=True,
                )
                user.set_password(form.cleaned_data['password'])
                user.save()
                EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
                messages.success(request, f"New staff account created for {user.first_name} ({user.get_role_display()})!")
                return redirect('dashboard:users')
    else:
        form = StaffCreationForm()

    return render(request, 'dashboard/staff_form.html', {'form': form})

@staff_required
def user_toggle_status_view(request, pk):
    """(Super Admin): Toggle active or suspended status for staff or customer."""
    if not request.user.is_admin_user():
        messages.error(request, "Access restricted to Super Admin.")
        return redirect('dashboard:home')
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, "You cannot suspend your own Super Admin account.")
    else:
        user_obj.is_active = not user_obj.is_active
        user_obj.save()
        status_word = "Activated" if user_obj.is_active else "Suspended"
        messages.info(request, f"User {user_obj.email} has been {status_word}.")
    return redirect('dashboard:users')
