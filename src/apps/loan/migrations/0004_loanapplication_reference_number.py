# Generated by Django 5.1.6 on 2025-04-09 20:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loan', '0003_loanapplication'),
    ]

    operations = [
        migrations.AddField(
            model_name='loanapplication',
            name='reference_number',
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
    ]
