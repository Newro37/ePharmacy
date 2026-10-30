from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Sum, Avg, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from allauth.account.models import EmailAddress
from apps.catalog.models import Medicine, Category, Manufacturer
from apps.cart.models import Order
from apps.payments.models import Payment
from apps.prescriptions.models import Prescription
from .forms import MedicineForm, StaffCreationForm

User = get_user_model()

# ============================================================================
# DECORATORS FOR ROLE-BASED ACCESS CONTROL
# ============================================================================

def customer_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_customer():
            messages.error(request, "Access restricted to customers only.")
            return redirect('catalog:home')
        return view_func(request, *args, **kwargs)
    return wrapper

def pharmacist_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_pharmacist():
            messages.error(request, "Access restricted to licensed pharmacists only.")
            return redirect('catalog:home')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin_user():
            messages.error(request, "Access restricted to Super Admin only.")
            return redirect('catalog:home')
        return view_func(request, *args, **kwargs)
    return wrapper

def staff_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_pharmacist() or request.user.is_admin_user()):
            messages.error(request, "Access restricted to authorized pharmacy staff.")
            return redirect('catalog:home')
        return view_func(request, *args, **kwargs)
    return wrapper

# ============================================================================
# ROLE-BASED DASHBOARD ROUTER
# ============================================================================

@login_required
def dashboard_home_view(request):
    """Route users to their role-specific dashboard."""
    user = request.user
    
    if user.is_admin_user():
        return redirect('dashboard:admin_dashboard')
    elif user.is_pharmacist():
        return redirect('dashboard:pharmacist_dashboard')
    elif user.is_customer():
        return redirect('dashboard:customer_dashboard')
    else:
        messages.error(request, "Your account role is not recognized.")
        return redirect('catalog:home')

# ============================================================================
# CUSTOMER DASHBOARD VIEWS
# ============================================================================

@customer_required
def customer_dashboard_view(request):
    """Customer Dashboard: Overview of orders, prescriptions, and account."""
    user = request.user
    
    # Order statistics
    total_orders = user.orders.count()
    pending_orders = user.orders.filter(status=Order.Status.PENDING).count()
    processing_orders = user.orders.filter(status=Order.Status.PROCESSING).count()
    delivered_orders = user.orders.filter(status=Order.Status.DELIVERED).count()
    
    # Recent orders
    recent_orders = user.orders.all().order_by('-created_at')[:5]
    
    # Prescription statistics
    total_prescriptions = user.prescriptions.count()
    pending_prescriptions = user.prescriptions.filter(status=Prescription.Status.PENDING).count()
    approved_prescriptions = user.prescriptions.filter(status=Prescription.Status.APPROVED).count()
    recent_prescriptions = user.prescriptions.all().order_by('-created_at')[:3]
    
    # Cart info
    cart_items_count = user.cart.get_item_count() if hasattr(user, 'cart') else 0
    
    # Address info
    addresses_count = user.addresses.count()
    
    return render(request, 'dashboard/customer_dashboard.html', {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'delivered_orders': delivered_orders,
        'recent_orders': recent_orders,
        'total_prescriptions': total_prescriptions,
        'pending_prescriptions': pending_prescriptions,
        'approved_prescriptions': approved_prescriptions,
        'recent_prescriptions': recent_prescriptions,
        'cart_items_count': cart_items_count,
        'addresses_count': addresses_count,
    })

# ============================================================================
# PHARMACIST DASHBOARD VIEWS
# ============================================================================

@pharmacist_required
def pharmacist_dashboard_view(request):
    """Pharmacist Dashboard: Prescription review, inventory, and order processing."""
    
    # Prescription Queue Statistics
    pending_prescriptions_count = Prescription.objects.filter(status=Prescription.Status.PENDING).count()
    approved_today = Prescription.objects.filter(
        status=Prescription.Status.APPROVED,
        reviewed_at__date=timezone.now().date()
    ).count()
    rejected_today = Prescription.objects.filter(
        status=Prescription.Status.REJECTED,
        reviewed_at__date=timezone.now().date()
    ).count()
    
    # Order Processing Statistics
    pending_orders = Order.objects.filter(status=Order.Status.PENDING).count()
    processing_orders = Order.objects.filter(status=Order.Status.PROCESSING).count()
    orders_today = Order.objects.filter(created_at__date=timezone.now().date()).count()
    
    # Inventory Alerts
    low_stock_medicines = Medicine.objects.low_stock(threshold=10)
    low_stock_count = low_stock_medicines.count()
    
    # Expired and Near-Expiry Medicines
    today = timezone.now().date()
    thirty_days_later = today + timedelta(days=30)
    expired_medicines = Medicine.objects.filter(expiry_date__lt=today).count()
    near_expiry_medicines = Medicine.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=thirty_days_later
    ).count()
    
    # Recent Activity
    recent_prescriptions = Prescription.objects.filter(
        status=Prescription.Status.PENDING
    ).order_by('created_at')[:5]
    
    recent_orders = Order.objects.filter(
        status__in=[Order.Status.PENDING, Order.Status.PROCESSING]
    ).order_by('-created_at')[:5]
    
    # Total medicines in inventory
    total_medicines = Medicine.objects.filter(is_active=True).count()
    
    return render(request, 'dashboard/pharmacist_dashboard.html', {
        'pending_prescriptions_count': pending_prescriptions_count,
        'approved_today': approved_today,
        'rejected_today': rejected_today,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'orders_today': orders_today,
        'low_stock_count': low_stock_count,
        'low_stock_medicines': low_stock_medicines[:6],
        'expired_medicines': expired_medicines,
        'near_expiry_medicines': near_expiry_medicines,
        'recent_prescriptions': recent_prescriptions,
        'recent_orders': recent_orders,
        'total_medicines': total_medicines,
    })

# ============================================================================
# SUPER ADMIN DASHBOARD VIEWS
# ============================================================================

@admin_required
def admin_dashboard_view(request):
    """Super Admin Dashboard: Complete platform overview and management."""
    
    # User Statistics
    total_customers = User.objects.filter(role=User.Role.CUSTOMER).count()
    total_pharmacists = User.objects.filter(role=User.Role.PHARMACIST).count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_this_month = User.objects.filter(
        date_joined__gte=timezone.now().replace(day=1)
    ).count()
    
    # Medicine & Inventory Statistics
    total_medicines = Medicine.objects.count()
    active_medicines = Medicine.objects.filter(is_active=True).count()
    low_stock_count = Medicine.objects.low_stock(threshold=10).count()
    
    today = timezone.now().date()
    expired_medicines = Medicine.objects.filter(expiry_date__lt=today).count()
    
    # Order Statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status=Order.Status.PENDING).count()
    processing_orders = Order.objects.filter(status=Order.Status.PROCESSING).count()
    completed_orders = Order.objects.filter(status=Order.Status.DELIVERED).count()
    cancelled_orders = Order.objects.filter(status=Order.Status.CANCELLED).count()
    
    # Financial Statistics
    settled_orders = Order.objects.exclude(status=Order.Status.CANCELLED)
    gross_revenue = settled_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    avg_order_value = settled_orders.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')
    
    # Revenue by payment method
    cod_revenue = Payment.objects.filter(
        method=Payment.Method.COD,
        status=Payment.Status.COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    online_revenue = Payment.objects.filter(
        method=Payment.Method.CARD_MOCK,
        status=Payment.Status.COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Daily, Weekly, Monthly revenue
    today = timezone.now().date()
    revenue_today = Order.objects.filter(
        created_at__date=today,
        status=Order.Status.DELIVERED
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    week_ago = today - timedelta(days=7)
    revenue_this_week = Order.objects.filter(
        created_at__date__gte=week_ago,
        status=Order.Status.DELIVERED
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    month_start = timezone.now().replace(day=1).date()
    revenue_this_month = Order.objects.filter(
        created_at__date__gte=month_start,
        status=Order.Status.DELIVERED
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    # Prescription Statistics
    total_prescriptions = Prescription.objects.count()
    pending_prescriptions = Prescription.objects.filter(status=Prescription.Status.PENDING).count()
    approved_prescriptions = Prescription.objects.filter(status=Prescription.Status.APPROVED).count()
    
    # Recent Activity
    recent_orders = Order.objects.all().order_by('-created_at')[:8]
    recent_users = User.objects.filter(role=User.Role.CUSTOMER).order_by('-date_joined')[:5]
    
    # Low stock medicines
    low_stock_medicines = Medicine.objects.low_stock(threshold=10)[:6]
    
    return render(request, 'dashboard/admin_dashboard.html', {
        'total_customers': total_customers,
        'total_pharmacists': total_pharmacists,
        'active_users': active_users,
        'new_users_this_month': new_users_this_month,
        'total_medicines': total_medicines,
        'active_medicines': active_medicines,
        'low_stock_count': low_stock_count,
        'expired_medicines': expired_medicines,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'gross_revenue': gross_revenue,
        'avg_order_value': avg_order_value,
        'cod_revenue': cod_revenue,
        'online_revenue': online_revenue,
        'revenue_today': revenue_today,
        'revenue_this_week': revenue_this_week,
        'revenue_this_month': revenue_this_month,
        'total_prescriptions': total_prescriptions,
        'pending_prescriptions': pending_prescriptions,
        'approved_prescriptions': approved_prescriptions,
        'recent_orders': recent_orders,
        'recent_users': recent_users,
        'low_stock_medicines': low_stock_medicines,
    })

# ============================================================================
# MEDICINE & INVENTORY MANAGEMENT (Pharmacist & Admin)
# ============================================================================

@staff_required
def medicine_list_view(request):
    """(Pharmacist & Admin): View and manage medicine inventory."""
    medicines = Medicine.objects.all().order_by('name')
    
    # Filter options
    search_query = request.GET.get('q', '').strip()
    if search_query:
        medicines = medicines.filter(
            Q(name__icontains=search_query) |
            Q(generic_name__icontains=search_query)
        )
    
    stock_filter = request.GET.get('stock', '')
    if stock_filter == 'low':
        medicines = medicines.filter(stock__lte=10)
    elif stock_filter == 'out':
        medicines = medicines.filter(stock=0)
    
    return render(request, 'dashboard/medicine_list.html', {
        'medicines': medicines,
        'search_query': search_query,
        'stock_filter': stock_filter,
    })

@staff_required
def medicine_create_view(request):
    """(Super Admin & Pharmacist): Add new medicine to inventory."""
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES)
        if form.is_valid():
            medicine = form.save()
            messages.success(request, f"Added {medicine.name} to pharmacy catalog & inventory.")
            return redirect('dashboard:medicine_list')
    else:
        form = MedicineForm()
    return render(request, 'dashboard/medicine_form.html', {
        'form': form,
        'title': 'Add New Medicine & Set Pricing'
    })

@staff_required
def medicine_update_view(request, pk):
    """(Super Admin & Pharmacist): Update medicine stock, pricing, and details."""
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated {medicine.name} inventory, batch, and pricing.")
            return redirect('dashboard:medicine_list')
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'dashboard/medicine_form.html', {
        'form': form,
        'title': f'Edit & Update {medicine.name}'
    })

@staff_required
def medicine_toggle_active_view(request, pk):
    """Toggle medicine active status."""
    medicine = get_object_or_404(Medicine, pk=pk)
    medicine.is_active = not medicine.is_active
    medicine.save()
    status_str = "activated" if medicine.is_active else "deactivated"
    messages.info(request, f"{medicine.name} has been {status_str}.")
    return redirect('dashboard:medicine_list')

# ============================================================================
# ORDER MANAGEMENT (Pharmacist & Admin)
# ============================================================================

@staff_required
def order_pipeline_view(request):
    """(Pharmacist & Admin): View and manage order fulfillment pipeline."""
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
    """(Pharmacist): Mark order as fulfilled and processing."""
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        order.status = Order.Status.PROCESSING
        order.save()
        messages.success(request, f"Order #{order.pk} marked as FULFILLED & IN PROCESSING.")
    return redirect('dashboard:orders')

@staff_required
def order_dispatch_view(request, pk):
    """(Pharmacist): Dispatch order for delivery."""
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        order.status = Order.Status.SHIPPED
        order.save()
        messages.success(request, f"Order #{order.pk} DISPATCHED with courier delivery.")
    return redirect('dashboard:orders')

@staff_required
def order_deliver_view(request, pk):
    """(Pharmacist & Admin): Mark order as delivered."""
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        order.status = Order.Status.DELIVERED
        order.save()
        messages.success(request, f"Order #{order.pk} successfully DELIVERED to patient.")
    return redirect('dashboard:orders')

# ============================================================================
# USER & STAFF MANAGEMENT (Super Admin Only)
# ============================================================================

@admin_required
def user_management_view(request):
    """(Super Admin): Manage customers and pharmacist accounts."""
    users = User.objects.all().order_by('-date_joined')
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    pharmacist_count = User.objects.filter(role=User.Role.PHARMACIST).count()
    customer_count = User.objects.filter(role=User.Role.CUSTOMER).count()
    admin_count = User.objects.filter(role=User.Role.ADMIN).count()
    
    return render(request, 'dashboard/users.html', {
        'users': users,
        'pharmacist_count': pharmacist_count,
        'customer_count': customer_count,
        'admin_count': admin_count,
        'role_filter': role_filter,
        'search_query': search_query,
    })

@admin_required
def staff_create_view(request):
    """(Super Admin): Create new pharmacist staff account."""
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

@admin_required
def user_toggle_status_view(request, pk):
    """(Super Admin): Toggle user active/suspended status."""
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, "You cannot suspend your own Super Admin account.")
    else:
        user_obj.is_active = not user_obj.is_active
        user_obj.save()
        status_word = "Activated" if user_obj.is_active else "Suspended"
        messages.info(request, f"User {user_obj.email} has been {status_word}.")
    return redirect('dashboard:users')

@admin_required
def user_delete_view(request, pk):
    """(Super Admin): Delete user account."""
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, "You cannot delete your own account.")
    elif user_obj.is_admin_user():
        messages.error(request, "Cannot delete administrator accounts through this interface.")
    else:
        email = user_obj.email
        user_obj.delete()
        messages.success(request, f"User account {email} has been permanently deleted.")
    return redirect('dashboard:users')

# ============================================================================
# REPORTS & ANALYTICS (Super Admin)
# ============================================================================

@admin_required
def sales_report_view(request):
    """(Super Admin): View detailed sales and revenue reports."""
    # Date filtering
    period = request.GET.get('period', 'all')
    today = timezone.now().date()
    
    if period == 'today':
        start_date = today
        orders = Order.objects.filter(created_at__date=today, status=Order.Status.DELIVERED)
    elif period == 'week':
        start_date = today - timedelta(days=7)
        orders = Order.objects.filter(created_at__date__gte=start_date, status=Order.Status.DELIVERED)
    elif period == 'month':
        start_date = timezone.now().replace(day=1).date()
        orders = Order.objects.filter(created_at__date__gte=start_date, status=Order.Status.DELIVERED)
    else:
        start_date = None
        orders = Order.objects.filter(status=Order.Status.DELIVERED)
    
    # Calculate metrics
    total_orders = orders.count()
    total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    avg_order_value = orders.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')
    
    # Revenue by payment method
    order_ids = orders.values_list('id', flat=True)
    cod_revenue = Payment.objects.filter(
        order_id__in=order_ids,
        method=Payment.Method.COD,
        status=Payment.Status.COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    online_revenue = Payment.objects.filter(
        order_id__in=order_ids,
        method=Payment.Method.CARD_MOCK,
        status=Payment.Status.COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    return render(request, 'dashboard/sales_report.html', {
        'period': period,
        'start_date': start_date,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'cod_revenue': cod_revenue,
        'online_revenue': online_revenue,
        'orders': orders[:50],  # Show recent orders
    })

@admin_required
def inventory_report_view(request):
    """(Super Admin): View comprehensive inventory reports."""
    # Stock analysis
    total_medicines = Medicine.objects.count()
    active_medicines = Medicine.objects.filter(is_active=True).count()
    inactive_medicines = Medicine.objects.filter(is_active=False).count()
    
    low_stock_medicines = Medicine.objects.low_stock(threshold=10)
    out_of_stock_medicines = Medicine.objects.filter(stock=0)
    
    # Expiry analysis
    today = timezone.now().date()
    thirty_days_later = today + timedelta(days=30)
    
    expired_medicines = Medicine.objects.filter(expiry_date__lt=today)
    near_expiry_medicines = Medicine.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=thirty_days_later
    )
    
    # Total stock value
    total_stock_value = Medicine.objects.aggregate(
        total=Sum(F('price') * F('stock'))
    )['total'] or Decimal('0.00')
    
    return render(request, 'dashboard/inventory_report.html', {
        'total_medicines': total_medicines,
        'active_medicines': active_medicines,
        'inactive_medicines': inactive_medicines,
        'low_stock_medicines': low_stock_medicines,
        'out_of_stock_medicines': out_of_stock_medicines,
        'expired_medicines': expired_medicines,
        'near_expiry_medicines': near_expiry_medicines,
        'total_stock_value': total_stock_value,
    })
