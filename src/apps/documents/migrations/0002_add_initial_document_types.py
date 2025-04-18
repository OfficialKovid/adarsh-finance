from django.db import migrations

def create_document_types(apps, schema_editor):
    DocumentType = apps.get_model('documents', 'DocumentType')
    
    # Only create if no document types exist
    if DocumentType.objects.count() == 0:
        document_types = [
            {'name': 'PDF Document', 'extension': 'pdf'},
            {'name': 'JPEG Image', 'extension': 'jpg'},
            {'name': 'PNG Image', 'extension': 'png'},
            {'name': 'Word Document', 'extension': 'docx'},
            {'name': 'Excel Sheet', 'extension': 'xlsx'},
        ]
        
        for doc_type in document_types:
            DocumentType.objects.create(**doc_type)

class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_document_types),
    ]
