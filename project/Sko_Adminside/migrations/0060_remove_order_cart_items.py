# Generated by Django 5.1.2 on 2024-11-24 15:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Sko_Adminside', '0059_order_cart_items'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='cart_items',
        ),
    ]
