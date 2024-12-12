from django.contrib import admin

from .models import (Task, Department, Role, Status)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "department_name"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "task_name"]

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "role_name"]

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "status"]