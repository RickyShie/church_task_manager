from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from .models import (Department, Teacher, Schedule, Position, ClassRole, RoleAssignment, HymnType)
from datetime import timedelta, datetime

WORSHIP_CLASS = "崇拜"
HYMN_CLASS = "詩頌"
ACTIVITY = "共習"

PRE_KINDERGARTEN = "幼幼班"
KINDERGARTEN = "幼稚班"
ELEMENTARY_1 = "幼年班"
ELEMENTARY_1_CN_JP = "幼年班(中日文)"
ELEMENTARY_2 = "少年班"
JUNIOR = "青教組"
JAPANESE = "日文班"
PIANICA = "口風琴班"
SHIKOYASU = "新子安"

STRPTIME_FORMAT = "%H:%M"


def is_odd_saturday(given_saturday):
    """
    Determines whether a given Saturday is the nth Saturday of the month where n%2 == 1.
    Returns True if it is odd, False if even.
    """
    # Ensure the given date is a Saturday
    if given_saturday.weekday() != 5:  # 5 = Saturday
        raise ValueError("The given date is not a Saturday.")

    # Find the first day of the month
    first_day_of_month = given_saturday.replace(day=1)

    # Calculate the first Saturday of the month
    days_to_first_saturday = (5 - first_day_of_month.weekday()) % 7
    first_saturday = first_day_of_month + timedelta(days=days_to_first_saturday)

    # Calculate how many Saturdays have passed
    count = 1
    current_saturday = first_saturday
    while current_saturday < given_saturday:
        current_saturday += timedelta(days=7)
        count += 1

    # Check if n (count) is odd
    return count % 2 == 1


def create_schedule_if_not_exists(date, department, start_time, end_time, class_type):
    """
    Helper function to check if a schedule exists and create it if it does not.
    """
    if not Schedule.objects.filter(date=date, department=department, class_type=class_type).exists():
        Schedule.objects.get_or_create(
            department=department,
            date=date,
            start_time=datetime.strptime(start_time, '%H:%M').time(),
            end_time=datetime.strptime(end_time, '%H:%M').time(),
            class_type=class_type
        )

@admin.action(description="Generate Schedules for Upcoming Saturdays")
def generate_schedules(modeladmin, request, queryset):
    departments = Department.objects.all()
    today = datetime.today().date()

    # Calculate the number of days to the next Saturday
    days_to_next_saturday = (5 - today.weekday()) % 7 + 7

    # Generate the next 12 Saturdays
    saturdays = [
        today + timedelta(days=days_to_next_saturday + i * 7)
        for i in range(14)
    ]

    # Class Type constants
    WORSHIP_CLASS = '崇拜'
    ACTIVITY = '共習'
    HYMN_CLASS = '詩頌'

    for date in saturdays:
        for department in departments:
            if department.name == PRE_KINDERGARTEN:
                create_schedule_if_not_exists(date, department, '14:00', '14:30', WORSHIP_CLASS)
                create_schedule_if_not_exists(date, department, '14:40', '15:00', ACTIVITY)

            elif department.name == KINDERGARTEN:
                create_schedule_if_not_exists(date, department, '11:30', '12:00', HYMN_CLASS)
                create_schedule_if_not_exists(date, department, '14:00', '14:35', WORSHIP_CLASS)
                create_schedule_if_not_exists(date, department, '14:40', '15:00', ACTIVITY)

            elif department.name in [ELEMENTARY_1, ELEMENTARY_1_CN_JP, ELEMENTARY_2, JUNIOR, JAPANESE]:
                create_schedule_if_not_exists(date, department, '14:00', '14:55', WORSHIP_CLASS)

                if department.name in [JUNIOR, JAPANESE]:
                    create_schedule_if_not_exists(date, department, '15:00', '15:30', ACTIVITY)

                # Handle odd/even Saturday logic
                if is_odd_saturday(date):
                    if department.name in [ELEMENTARY_1, ELEMENTARY_1_CN_JP]:
                        create_schedule_if_not_exists(date, department, '15:00', '15:30', HYMN_CLASS)
                    elif department.name == ELEMENTARY_2:
                        create_schedule_if_not_exists(date, department, '15:00', '15:30', ACTIVITY)
                else:  # Even Saturday logic
                    if department.name in [ELEMENTARY_1, ELEMENTARY_1_CN_JP]:
                        create_schedule_if_not_exists(date, department, '15:00', '15:30', ACTIVITY)
                    elif department.name == ELEMENTARY_2:
                        create_schedule_if_not_exists(date, department, '15:00', '15:30', HYMN_CLASS)



@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "name", "description"]

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Personal Information", {"fields": ("name", "gender", "region")}),
        ("Professional Information", {"fields": ("status", "department", "position")})
    )
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


@admin.register(ClassRole)
class ClassRoleAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "name"]


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "person", "role", "schedule__date",
                    "schedule__department__name", "schedule__class_type"]
    list_filter = [
        ("schedule__date", DateFieldListFilter), # Add a date filter for the schedule's date
        "schedule__department__name",
        "schedule__class_type",
        "role",
        "person"
    ]
    actions = ["delete_selected"]
    search_fields = ["person__name", "role__name", "schedule__date"]  # Include date in the search fields
    date_hierarchy = "schedule__date"

    # Enable live search for the 'schedule' field
    autocomplete_fields = ["schedule"]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = [
        "id",
        "date",
        "start_time",
        "end_time",
        "department",
        "class_type",
        "topic",
        "hymn_type",
        "hymn_number",
        "get_role_assignments"
    ]
    list_editable = ["date"]
    list_filter = [("date", DateFieldListFilter), "department", "class_type"]
    date_hierarchy = "date"
    actions = [generate_schedules]
    search_fields = ["date", "department__name", "class_type"]

    def get_role_assignments(self, obj):
        """
        Returns a formatted string of all RoleAssignment objects attached to this schedule.
        """
        role_assignments = obj.role_assignments.all()
        return ", ".join(
            f"{assignment.role.name}: {assignment.person.name if assignment.person else 'Unassigned'}"
            for assignment in role_assignments
        )
    get_role_assignments.short_description = "Role Assignments"

@admin.register(HymnType)
class HymnTypeAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = ["id", "name", "description"]
    list_editable = ["description"]