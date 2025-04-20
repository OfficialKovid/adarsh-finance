from django.db import models
from apps.loan.models import LoanScheme, LoanApplication
from django.conf import settings

class FormSubmission(models.Model):
    application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE)
    scheme = models.ForeignKey(LoanScheme, on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()  # Stores the form field values
    files = models.JSONField(default=dict)  # Stores file paths

    def __str__(self):
        return f"Form submission for {self.application.reference_number}"

    class Meta:
        ordering = ['-submitted_at']
