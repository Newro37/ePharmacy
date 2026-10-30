from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail_view, name='cart_detail'),
    path('add/<int:medicine_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart_item_view, name='update_cart_item'),
    path('remove/<int:item_id>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('orders/', views.order_list_view, name='order_list'),
    path('order/<int:order_id>/cancel/', views.cancel_order_view, name='cancel_order'),
]
