from django.contrib import admin
from .models import LoanScheme, Benefit, EligibilityCriteria, RequiredDocument, CoveredSector, ServiceOffered, LoanApplication

@admin.register(LoanScheme)
class LoanSchemeAdmin(admin.ModelAdmin):
    list_display = ['title', 'full_name', 'is_active', 'created_at']  # changed from short_name to full_name
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'full_name', 'description']  # changed from short_name to full_name
    prepopulated_fields = {'slug': ('title',)}

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'scheme', 'status', 'applied_at']
    list_filter = ['status', 'applied_at', 'scheme']
    search_fields = ['name', 'phone_number', 'scheme__title']
    readonly_fields = ['applied_at']
    ordering = ['-applied_at']

admin.site.register(Benefit)
admin.site.register(EligibilityCriteria)
admin.site.register(RequiredDocument)
admin.site.register(CoveredSector)
admin.site.register(ServiceOffered)
