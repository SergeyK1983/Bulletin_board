# Generated by Django 4.2.7 on 2024-02-11 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('announcement', '0003_alter_post_files_alter_post_images'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='article',
            field=models.TextField(max_length=5000, verbose_name='Содержание'),
        ),
    ]