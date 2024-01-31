# Generated by Django 4.2.7 on 2024-01-31 08:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('announcement', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentaryToAuthor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(max_length=500, verbose_name='Комментарий')),
                ('accepted', models.BooleanField(default=False, verbose_name='Принято')),
                ('date_create', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment', to=settings.AUTH_USER_MODEL, to_field='username', verbose_name='Автор комментария')),
                ('to_post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment', to='announcement.post', to_field='title', verbose_name='На публикацию')),
            ],
            options={
                'verbose_name': 'Отклик автору',
                'verbose_name_plural': 'Отклики автору',
                'ordering': ['id'],
            },
        ),
    ]
