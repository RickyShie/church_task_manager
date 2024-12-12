from django.contrib import admin
from .models import (Department, Teacher, Schedule, Activity, RoleAssignment)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "name", "description"]

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "status", "department", "role", "name", "gender"]
    actions = ["delete_selected"]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "date", "start_time", "end_time", "department", "class_type", "topic"]
    actions = ["delete_selected"]


# @admin.register(Activity)
# class ActivityAdmin(admin.ModelAdmin):
#     ordering = ["id"]
#     list_display = ["id", "class_type", "details", "schedule"]


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "person", "role", "schedule"]
    actions = ["delete_selected"]