from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    path('upload/', views.upload_prescription_view, name='upload'),
    path('my/', views.my_prescriptions_view, name='my_prescriptions'),
    path('<int:pk>/', views.prescription_detail_view, name='detail'),
    path('review/', views.review_list_view, name='review_list'),
    path('review/<int:pk>/', views.review_detail_view, name='review_detail'),
]
