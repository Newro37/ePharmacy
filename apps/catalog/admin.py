from django.contrib import admin
from .models import Category, Manufacturer, Medicine

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'website')

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'dosage', 'price', 'stock', 'prescription_required', 'is_active')
    list_filter = ('prescription_required', 'is_active', 'category')
    search_fields = ('name', 'dosage', 'description')
    prepopulated_fields = {'slug': ('name',)}
