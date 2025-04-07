from django.db import models
from django.utils.text import slugify

class LoanScheme(models.Model):
    title = models.CharField(max_length=255)
    full_name = models.CharField(max_length=100, blank=True, null=True)  # renamed from short_name
    description = models.TextField()
    start_year = models.PositiveIntegerField(blank=True, null=True)  # made optional
    end_year = models.PositiveIntegerField(blank=True, null=True)    # made optional
    contact_info = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='media/loan_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional: Auto-generate slug
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title



class Benefit(models.Model):
    scheme = models.ForeignKey(LoanScheme, related_name='benefits', on_delete=models.CASCADE)
    description = models.TextField()

    def __str__(self):
        return f"Benefit for {self.scheme.title}"


class EligibilityCriteria(models.Model):
    scheme = models.ForeignKey(LoanScheme, related_name='eligibility_criteria', on_delete=models.CASCADE)
    criteria = models.TextField()

    def __str__(self):
        return f"Eligibility for {self.scheme.title}"


class RequiredDocument(models.Model):
    scheme = models.ForeignKey(LoanScheme, related_name='required_documents', on_delete=models.CASCADE)
    document_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.document_name} for {self.scheme.title}"


class CoveredSector(models.Model):
    scheme = models.ForeignKey(LoanScheme, related_name='covered_sectors', on_delete=models.CASCADE)
    sector_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.sector_name} - {self.scheme.title}"


class ServiceOffered(models.Model):
    scheme = models.ForeignKey(LoanScheme, related_name='services_offered', on_delete=models.CASCADE)
    service_description = models.TextField()

    def __str__(self):
        return f"Service for {self.scheme.title}"


class KeyPoint(models.Model):
    scheme = models.ForeignKey(LoanScheme, related_name='key_points', on_delete=models.CASCADE)
    point = models.CharField(max_length=255)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"Key point for {self.scheme.title}"
