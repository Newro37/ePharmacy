from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home_view, name='home'),
    path('medicines/', views.medicine_list_view, name='medicine_list'),
    path('medicines/add/', views.medicine_create_view, name='medicine_create'),
    path('medicines/<int:pk>/edit/', views.medicine_update_view, name='medicine_update'),
    path('medicines/<int:pk>/toggle/', views.medicine_toggle_active_view, name='medicine_toggle'),
    path('orders/', views.order_pipeline_view, name='orders'),
    path('orders/<int:pk>/status/', views.order_status_update_view, name='order_status_update'),
    path('users/', views.user_management_view, name='users'),
]
