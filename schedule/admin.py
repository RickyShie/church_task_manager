from django.contrib import admin

from .models import (Task, Department, Role)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "department_name"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "task_name"]