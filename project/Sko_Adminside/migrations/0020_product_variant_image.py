# Generated by Django 5.1.2 on 2024-10-28 11:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Sko_Adminside', '0019_variants_varientimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='variant_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='Sko_Adminside.varientimage'),
        ),
    ]
