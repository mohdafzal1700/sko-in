# Generated by Django 5.1.2 on 2024-11-26 07:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Sko_Adminside', '0063_remove_cart_coupon_transaction_wallet'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wallet',
            name='user',
        ),
        migrations.DeleteModel(
            name='Transaction',
        ),
        migrations.DeleteModel(
            name='Wallet',
        ),
    ]
