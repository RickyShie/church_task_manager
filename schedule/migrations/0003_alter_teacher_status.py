# Generated by Django 5.1.4 on 2024-12-12 13:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("schedule", "0002_alter_teacher_department_alter_teacher_position"),
    ]

    operations = [
        migrations.AlterField(
            model_name="teacher",
            name="status",
            field=models.CharField(
                choices=[
                    ("Active", "Active"),
                    ("Inactive", "Inactive"),
                    ("New", "New"),
                ],
                default="Active",
                max_length=50,
            ),
        ),
    ]