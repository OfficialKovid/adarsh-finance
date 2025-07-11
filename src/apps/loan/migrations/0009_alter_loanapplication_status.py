# Generated by Django 5.1.6 on 2025-04-10 05:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loan', '0008_alter_loanapplication_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanapplication',
            name='status',
            field=models.CharField(choices=[('new_lead', 'New Lead'), ('not_converted', 'Not Converted'), ('assigned', 'Assigned'), ('detail_collection', 'Detail Collection'), ('form_filled', 'Form Filled'), ('under_review', 'Under Review'), ('closed', 'Closed'), ('dropped', 'Dropped')], default='new_lead', max_length=20),
        ),
    ]
