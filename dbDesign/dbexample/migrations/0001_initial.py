# Generated by Django 3.2 on 2022-09-29 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='required, max_len: 100', max_length=100, unique=True, verbose_name='product category name')),
                ('slug', models.SlugField(help_text='required, allowed=[letters, numbers, hyphens, underscore], max_len: 150', max_length=150, unique=True, verbose_name='product category url')),
                ('is_active', models.BooleanField(default=True, help_text='optional, defalut: True', verbose_name='product category active status')),
            ],
            options={
                'verbose_name': 'Product category',
                'verbose_name_plural': 'Product categories',
            },
        ),
    ]