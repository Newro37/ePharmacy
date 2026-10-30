from django.contrib import admin
from .models import Prescription

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'reviewed_by', 'reviewed_at', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'notes', 'review_notes')

