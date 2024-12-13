from django.contrib import admin
from .models import (Department, Teacher, Schedule, Position, RoleAssignment)
from .forms import RoleAssignmentInlineFormset

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
    search_fields = ["name", "region", "department__name", "position__name"]
    list_filter = ["status", "department", "gender", "region"]

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "name", "description"]
    actions = ["delete_selected"]


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "person", "role", "schedule"]
    actions = ["delete_selected"]


# Use Inline Models
class RoleAssignmentInline(admin.TabularInline):
    model = RoleAssignment
    formset = RoleAssignmentInlineFormset
    extra = 1

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "date", "start_time", "end_time", "department", "class_type", "topic"]
    list_editable = ["date"]
    inlines = [RoleAssignmentInline]  # Include RoleAssignment inline
    actions = ["delete_selected"]