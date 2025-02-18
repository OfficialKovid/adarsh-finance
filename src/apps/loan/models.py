from django.db import models

# Create your models here.
class LoanInfo(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    loan_type = models.CharField(max_length=100)
    loan_image = models.ImageField(upload_to='loan_images/', max_length=100)
    
    min_age = models.PositiveSmallIntegerField()
    max_age = models.PositiveSmallIntegerField()
    min_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    yearly_interest = models.PositiveSmallIntegerField()
    tenure_months = models.PositiveSmallIntegerField()
    
    eligibility_criteria = models.TextField(max_length=500)
    loan_slug = models.SlugField(max_length=50, blank=True, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    