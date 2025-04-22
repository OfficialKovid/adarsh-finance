import uuid
from django.db import models
from django.utils.text import slugify
from django.conf import settings
from apps.documents.models import RequiredDocument  # Add this import
import random
import string
from .utils import encrypt_password, decrypt_password

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
            # Generate base slug from title
            base_slug = slugify(self.title)
            
            # Check if the slug exists
            slug = base_slug
            while LoanScheme.objects.filter(slug=slug).exists():
                # Add random suffix
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                slug = f"{base_slug}-{random_suffix}"
            
            self.slug = slug
            
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


class LoanApplication(models.Model):
    reference_number = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    scheme = models.ForeignKey(LoanScheme, on_delete=models.CASCADE, related_name='applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('new_lead', 'New Lead'),
            ('not_converted', 'Not Converted'),
            ('assigned', 'Assigned'),
            ('detail_collection', 'Detail Collection'),
            ('form_filled', 'Form Filled'),
            ('under_review', 'Under Review'),
            ('closed', 'Closed'),
            ('dropped', 'Dropped')  # Added new status
        ],
        default='new_lead'
    )
    notes = models.TextField(blank=True, null=True)
    is_registered = models.BooleanField(default=False)  # Add this field
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_applications'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_applications'
    )
    # Add these new fields
    loan_application_number = models.CharField(max_length=100, blank=True, null=True)
    loan_username = models.CharField(max_length=100, blank=True, null=True)
    loan_password = models.CharField(max_length=255, blank=True, null=True)  # Will be encrypted
    report = models.FileField(
        upload_to='loan_reports/%Y/%m/%d/', 
        null=True, 
        blank=True,
        help_text="Upload PDF report"
    )

    class Meta:
        ordering = ['-applied_at']

    def clean(self):
        if self.report and not self.report.name.endswith('.pdf'):
            raise ValidationError('Only PDF files are allowed for reports.')
    
    def save(self, *args, **kwargs):
        if self.report:
            self.clean()
        if not self.reference_number:
            # Generate reference number using UUID
            unique_id = str(uuid.uuid4())[:8].upper()
            self.reference_number = f'LA-{unique_id}'
        super().save(*args, **kwargs)

    def set_password(self, password):
        self.loan_password = encrypt_password(password)

    def get_password(self):
        return decrypt_password(self.loan_password)

    @classmethod
    def get_active_application(cls, user):
        """Get user's active loan application"""
        return cls.objects.filter(
            user=user,
            status__in=['new_lead', 'assigned', 'detail_collection', 'form_filled', 'under_review']
        ).select_related('scheme').first()

    @classmethod
    def get_by_reference(cls, reference_number):
        """Get application by reference number only if it's not already registered"""
        return cls.objects.filter(
            reference_number=reference_number,
            is_registered=False
        ).first()

    @classmethod
    def get_status_choices(cls):
        return [
            {'value': choice[0], 'label': choice[1]} 
            for choice in cls._meta.get_field('status').choices
        ]

    def __str__(self):
        return f"{self.name} - {self.scheme.title}"


class RequiredDataField(models.Model):
    FIELD_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('email', 'Email'),
        ('phone', 'Phone Number'),
        ('date', 'Date'),
        ('file', 'File Upload'),
        ('address', 'Address'),
        ('select', 'Select Options'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkbox'),
    ]

    scheme = models.ForeignKey(LoanScheme, related_name='required_data_fields', on_delete=models.CASCADE)
    field_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    options = models.TextField(blank=True, null=True, help_text="Comma-separated options for select/radio/checkbox fields")

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"{self.field_name} ({self.field_type}) - {self.scheme.title}"

