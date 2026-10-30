from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Cart, CartItem, Order, OrderItem
from apps.catalog.models import Medicine
from apps.accounts.models import Address
from apps.payments.models import Payment, PaymentContext, MockPaymentStrategy

def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart

@login_required
def cart_detail_view(request):
    cart = _get_or_create_cart(request.user)
    has_rx_items = any(item.medicine.prescription_required for item in cart.items.all())
    approved_rx_count = request.user.prescriptions.filter(status='approved').count()
    return render(request, 'cart/cart_detail.html', {
        'cart': cart,
        'has_rx_items': has_rx_items,
        'approved_rx_count': approved_rx_count,
    })

@login_required
def add_to_cart_view(request, medicine_id):
    medicine = get_object_or_404(Medicine, pk=medicine_id, is_active=True)
    if not medicine.is_in_stock:
        messages.error(request, f"{medicine.name} is currently out of stock.")
        return redirect('catalog:medicine_detail', slug=medicine.slug)

    cart = _get_or_create_cart(request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, medicine=medicine)
    if not created:
        if cart_item.quantity + 1 > medicine.stock:
            messages.warning(request, f"Cannot add more. Only {medicine.stock} units available.")
            return redirect('cart:cart_detail')
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"Added {medicine.name} to cart.")
    return redirect('cart:cart_detail')

@login_required
def update_cart_item_view(request, item_id):
    cart = _get_or_create_cart(request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    action = request.POST.get('action')
    if action == 'increase':
        if item.quantity + 1 <= item.medicine.stock:
            item.quantity += 1
            item.save()
        else:
            messages.warning(request, f"Maximum available stock is {item.medicine.stock}.")
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
            messages.info(request, f"Removed {item.medicine.name} from cart.")
    return redirect('cart:cart_detail')

@login_required
def remove_from_cart_view(request, item_id):
    cart = _get_or_create_cart(request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    name = item.medicine.name
    item.delete()
    messages.info(request, f"Removed {name} from cart.")
    return redirect('cart:cart_detail')

@login_required
def checkout_view(request):
    cart = _get_or_create_cart(request.user)
    if not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('catalog:medicine_list')

    # Validate prescription requirements
    has_rx = any(item.medicine.prescription_required for item in cart.items.all())
    if has_rx:
        approved = request.user.prescriptions.filter(status='approved').exists()
        if not approved:
            messages.error(request, "Your cart contains prescription medicines. Please upload a prescription and wait for pharmacist verification before checking out.")
            return redirect('prescriptions:upload')

    addresses = request.user.addresses.all()

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        new_street = request.POST.get('street', '').strip()
        new_city = request.POST.get('city', '').strip()
        payment_method = request.POST.get('payment_method', 'cod')

        if address_id:
            addr = get_object_or_404(Address, pk=address_id, user=request.user)
            delivery_address = f"{addr.street}, {addr.city}, {addr.district}"
        elif new_street and new_city:
            delivery_address = f"{new_street}, {new_city}"
        else:
            messages.error(request, "Please provide or select a delivery address.")
            return render(request, 'cart/checkout.html', {'cart': cart, 'addresses': addresses})

        with transaction.atomic():
            # Validate stock availability atomically
            for item in cart.items.select_related('medicine').all():
                if item.quantity > item.medicine.stock:
                    messages.error(request, f"Insufficient stock for {item.medicine.name}. Only {item.medicine.stock} left.")
                    return redirect('cart:cart_detail')

            total_amount = cart.get_total()
            order = Order.objects.create(
                user=request.user,
                total_amount=total_amount,
                delivery_address=delivery_address,
                notes=request.POST.get('notes', ''),
            )

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    medicine=item.medicine,
                    medicine_name=item.medicine.name,
                    unit_price=item.medicine.price,
                    quantity=item.quantity,
                )
                # Decrement stock atomically
                item.medicine.stock -= item.quantity
                item.medicine.save()

            # Execute Payment Strategy
            payment = Payment.objects.create(
                order=order,
                amount=total_amount,
                method=Payment.Method.CARD_MOCK if payment_method == 'card_mock' else Payment.Method.COD,
            )
            strategy = MockPaymentStrategy()
            context = PaymentContext(strategy)
            context.execute_payment(payment)

            # Clear cart
            cart.items.all().delete()

        messages.success(request, f"Order #{order.pk} placed successfully!")
        return redirect('cart:order_detail', order_id=order.pk)

    return render(request, 'cart/checkout.html', {
        'cart': cart,
        'addresses': addresses,
    })

@login_required
def order_detail_view(request, order_id):
    if request.user.is_admin_user() or request.user.is_pharmacist():
        order = get_object_or_404(Order, pk=order_id)
    else:
        order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'cart/order_detail.html', {'order': order})

@login_required
def order_list_view(request):
    orders = request.user.orders.all().order_by('-created_at')
    return render(request, 'cart/order_list.html', {'orders': orders})

@login_required
def cancel_order_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if order.can_cancel():
        with transaction.atomic():
            order.status = Order.Status.CANCELLED
            order.save()
            # Restock items
            for item in order.items.all():
                if item.medicine:
                    item.medicine.stock += item.quantity
                    item.medicine.save()
        messages.success(request, f"Order #{order.pk} has been cancelled.")
    else:
        messages.error(request, "Only pending orders can be cancelled.")
    return redirect('cart:order_detail', order_id=order.pk)
