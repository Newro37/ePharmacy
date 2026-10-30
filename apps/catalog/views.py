from django.shortcuts import render, get_object_or_404
from .models import Category, Medicine

def home_view(request):
    featured_medicines = Medicine.objects.available()[:8]
    categories = Category.objects.all()[:6]
    return render(request, 'home.html', {
        'featured_medicines': featured_medicines,
        'categories': categories,
    })

def medicine_list_view(request):
    queryset = Medicine.objects.available()
    categories = Category.objects.all()

    query = request.GET.get('q', '').strip()
    if query:
        queryset = queryset.search(query)

    category_slug = request.GET.get('category', '').strip()
    if category_slug:
        queryset = queryset.by_category(category_slug)

    prescription_only = request.GET.get('rx', '').strip()
    if prescription_only == '1':
        queryset = queryset.filter(prescription_required=True)
    elif prescription_only == '0':
        queryset = queryset.filter(prescription_required=False)

    return render(request, 'catalog/medicine_list.html', {
        'medicines': queryset,
        'categories': categories,
        'current_category': category_slug,
        'search_query': query,
        'rx_filter': prescription_only,
    })

def medicine_detail_view(request, slug):
    medicine = get_object_or_404(Medicine, slug=slug, is_active=True)
    related_medicines = Medicine.objects.available().filter(category=medicine.category).exclude(pk=medicine.pk)[:4]
    return render(request, 'catalog/medicine_detail.html', {
        'medicine': medicine,
        'related_medicines': related_medicines,
    })

