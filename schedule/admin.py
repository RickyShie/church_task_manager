from django.contrib import admin
from .models import (Department, Teacher, Schedule, Position, RoleAssignment)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "name", "description"]

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "status", "department", "position", "name", "gender", "region"]
    list_editable = ["status", "department", "position", "name", "gender", "region"]
    actions = ["delete_selected"]

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "name", "description"]
    actions = ["delete_selected"]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "date", "start_time", "end_time", "department", "class_type", "topic"]
    actions = ["delete_selected"]


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "person", "role", "schedule"]
    actions = ["delete_selected"]