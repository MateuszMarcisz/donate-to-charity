# Generated by Django 5.0.7 on 2024-07-17 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('charity_donations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='is_taken',
            field=models.BooleanField(default=False),
        ),
    ]