from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Role-based dashboard router
    path('', views.dashboard_home_view, name='home'),
    
    # Customer Dashboard
    path('customer/', views.customer_dashboard_view, name='customer_dashboard'),
    
    # Pharmacist Dashboard
    path('pharmacist/', views.pharmacist_dashboard_view, name='pharmacist_dashboard'),
    
    # Super Admin Dashboard
    path('admin/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # Medicine & Inventory Management (Pharmacist & Admin)
    path('medicines/', views.medicine_list_view, name='medicine_list'),
    path('medicines/add/', views.medicine_create_view, name='medicine_create'),
    path('medicines/<int:pk>/edit/', views.medicine_update_view, name='medicine_update'),
    path('medicines/<int:pk>/toggle/', views.medicine_toggle_active_view, name='medicine_toggle'),
    
    # Order Management (Pharmacist & Admin)
    path('orders/', views.order_pipeline_view, name='orders'),
    path('orders/<int:pk>/status/', views.order_status_update_view, name='order_status_update'),
    path('orders/<int:pk>/fulfill/', views.order_fulfill_view, name='order_fulfill'),
    path('orders/<int:pk>/dispatch/', views.order_dispatch_view, name='order_dispatch'),
    path('orders/<int:pk>/deliver/', views.order_deliver_view, name='order_deliver'),
    
    # User Management (Super Admin Only)
    path('users/', views.user_management_view, name='users'),
    path('staff/add/', views.staff_create_view, name='staff_add'),
    path('users/<int:pk>/toggle/', views.user_toggle_status_view, name='user_toggle'),
    path('users/<int:pk>/delete/', views.user_delete_view, name='user_delete'),
    
    # Reports & Analytics (Super Admin Only)
    path('reports/sales/', views.sales_report_view, name='sales_report'),
    path('reports/inventory/', views.inventory_report_view, name='inventory_report'),
]
