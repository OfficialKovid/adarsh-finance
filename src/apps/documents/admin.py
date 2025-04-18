from django.contrib import admin
from .models import DocumentType, RequiredDocument

class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'extension', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'extension')

class RequiredDocumentAdmin(admin.ModelAdmin):
    list_display = ('document_name', 'scheme', 'document_type', 'is_required')
    list_filter = ('document_type', 'is_required')
    search_fields = ('document_name', 'scheme__title')

admin.site.register(DocumentType, DocumentTypeAdmin)
admin.site.register(RequiredDocument, RequiredDocumentAdmin)
