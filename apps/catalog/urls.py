from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('catalog/', views.medicine_list_view, name='medicine_list'),
    path('medicine/<slug:slug>/', views.medicine_detail_view, name='medicine_detail'),
]
