# Generated by Django 5.1.4 on 2024-12-20 05:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("schedule", "0002_alter_activity_class_type_alter_schedule_class_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="schedule",
            name="lesson_number",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
