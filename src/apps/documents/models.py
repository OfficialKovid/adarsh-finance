from django.db import models

class DocumentType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    extension = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.extension})"

class RequiredDocument(models.Model):
    scheme = models.ForeignKey('loan.LoanScheme', related_name='required_documents', on_delete=models.CASCADE)
    document_name = models.CharField(max_length=100)
    document_type = models.ForeignKey(DocumentType, on_delete=models.SET_DEFAULT, default=1)
    is_required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.document_name} for {self.scheme.title}"

    class Meta:
        ordering = ['document_name']
