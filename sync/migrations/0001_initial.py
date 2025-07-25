# Generated by Django 4.2.22 on 2025-06-05 19:58

from django.db import migrations, models
import sync.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Deleted_Record',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_name', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('model_name', models.CharField(blank=True, max_length=100, null=True)),
                ('model_id', models.IntegerField(blank=True, null=True)),
                ('deleted', models.IntegerField(blank=True, default=0, null=True)),
                ('sync_unix', models.BigIntegerField(default=sync.models.current_unix_ms)),
            ],
        ),
    ]
