from django.contrib import admin
from .models import LoanScheme, Benefit, EligibilityCriteria, RequiredDocument, CoveredSector, ServiceOffered

@admin.register(LoanScheme)
class LoanSchemeAdmin(admin.ModelAdmin):
    list_display = ['title', 'full_name', 'is_active', 'created_at']  # changed from short_name to full_name
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'full_name', 'description']  # changed from short_name to full_name
    prepopulated_fields = {'slug': ('title',)}

admin.site.register(Benefit)
admin.site.register(EligibilityCriteria)
admin.site.register(RequiredDocument)
admin.site.register(CoveredSector)
admin.site.register(ServiceOffered)
