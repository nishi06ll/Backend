# Generated by Django 5.0.2 on 2024-05-08 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookingapi', '0003_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='booking_pdf',
        ),
        migrations.AddField(
            model_name='booking',
            name='qr_image',
            field=models.ImageField(blank=True, null=True, upload_to='QRCode'),
        ),
    ]
