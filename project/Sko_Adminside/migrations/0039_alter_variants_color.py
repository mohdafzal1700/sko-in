# Generated by Django 5.1.2 on 2024-11-14 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Sko_Adminside', '0038_order_shipping_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variants',
            name='color',
            field=models.CharField(choices=[('red', 'Red'), ('blue', 'Blue'), ('green', 'Green'), ('black', 'Black'), ('white', 'White'), ('yellow', 'Yellow'), ('purple', 'Purple'), ('gray', 'Gray'), ('pink', 'Pink'), ('orange', 'Orange')], max_length=50),
        ),
    ]
