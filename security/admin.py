from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'reporter_name', 'case_type', 'status', 'created_at')
    list_filter = ('status', 'case_type', 'is_anonymous')
    search_fields = ('reference_number', 'title', 'description', 'email')
    readonly_fields = ('reference_number', 'created_at', 'updated_at')
