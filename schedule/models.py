from django.db import models
from django.core.exceptions import ValidationError

# Department Model
class Department(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class Position(models.Model):
    name = models.CharField(max_length=200, unique=True)  # Position name, e.g., "Class Manager", "Teacher", "Assistant"
    description = models.TextField(null=True, blank=True)  # Optional description about the position

    def __str__(self):
        return self.name


# Teacher Model
class Teacher(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('New', 'New'),  # Adding the new tuple
    ]
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    name = models.CharField(max_length=200)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)  # Can be nullable
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)  # Can be nullable
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    region = models.CharField(max_length=200, null=True, blank=True)  # Optional: region or area

    def clean(self):
        """
        Enforce rules for department and position fields based on the status:
        - 'Active': department and position must NOT be blank.
        - 'New': department and position CAN be blank.
        - 'Inactive': department and position MUST be blank.
        """
        if self.status == 'Active':
            if not self.department or not self.position:
                raise ValidationError("Active teachers must have both a department and a position.")
        elif self.status == 'Inactive':
            if self.department or self.position:
                raise ValidationError("Inactive teachers must NOT have a department or position.")
        elif self.status == 'New':
            # 'New' teachers can have department and position left blank
            pass

    def save(self, *args, **kwargs):
        """
        Call clean before saving to validate constraints.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Schedule Model
class Schedule(models.Model):
    CLASS_TYPE_CHOICES = [
        ('崇拜', '崇拜'),
        ('詩頌', '詩頌'),
        ('共習', '共習'),
    ]

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    topic = models.CharField(max_length=500, null=True, blank=True)
    class_type = models.CharField(max_length=50, choices=CLASS_TYPE_CHOICES)

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be later than start time.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} ({self.start_time} - {self.end_time}) - {self.department} - {self.class_type}"


# Activity Model
class Activity(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    details = models.TextField(null=True, blank=True)
    class_type = models.CharField(max_length=50, choices=Schedule.CLASS_TYPE_CHOICES)

    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"

    def __str__(self):
        return f"{self.class_type} for {self.schedule}"


# RoleAssignment Model
class RoleAssignment(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    role = models.CharField(max_length=200)  # Role such as Teacher, Assistant, etc.
    person = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)

    def clean(self):
        """
        Prevent assigning a teacher to multiple tasks with overlapping time slots,
        and ensure a teacher can only have one role in a department on the same day.
        """
        # Ensure the schedule is not duplicated
        schedule_data = {
            'date': self.schedule.date,
            'start_time': self.schedule.start_time,
            'end_time': self.schedule.end_time,
            'department': self.schedule.department,
        }
        existing_schedule = Schedule.objects.filter(**schedule_data).exclude(id=self.schedule.id).exists()
        if existing_schedule:
            raise ValidationError("A scheduel with the same date, time, and department already exists.")

        if self.person:
            # Check for overlapping time slots
            conflicting_assignments = RoleAssignment.objects.filter(
                person=self.person,
                schedule__date=self.schedule.date,
                # Check overlapping time slots
                schedule__start_time__lt=self.schedule.end_time,
                schedule__end_time__gt=self.schedule.start_time
            ).exclude(id=self.id)  # Exclude the current instance being validated

            if conflicting_assignments.exists():
                conflict = conflicting_assignments.first()  # Get the first conflict
                department_name = conflict.schedule.department.name if conflict.schedule.department else "Unknown Department"
                role_name = conflict.role  # Retrieve the role name

                raise ValidationError(
                    f"{self.person.name} is already assigned as a '{role_name}' in the '{department_name}' department "
                    f"from {conflict.schedule.start_time} to {conflict.schedule.end_time}."
                )

            # Check if the teacher is assigned to another role in the same department on the same day
            same_department_assignments = RoleAssignment.objects.filter(
                person=self.person,
                schedule__date=self.schedule.date,
                schedule__department=self.schedule.department
            ).exclude(id=self.id)  # Exclude the current instance being validated

            if same_department_assignments.exists():
                existing_role = same_department_assignments.first().role
                department_name = self.schedule.department.name if self.schedule.department else "Unknown Department"

                raise ValidationError(
                    f"{self.person.name} is already assigned to the role '{existing_role}' in the '{department_name}' department "
                    f"on {self.schedule.date}. A teacher can only have one role per department per day."
                )

    def save(self, *args, **kwargs):
        """
        Call the validation method before saving.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.role} - {self.person.name if self.person else 'Unassigned'} for {self.schedule}"