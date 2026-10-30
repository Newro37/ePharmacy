from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('address/add/', views.address_create_view, name='address_add'),
    path('address/<int:pk>/delete/', views.address_delete_view, name='address_delete'),
]

