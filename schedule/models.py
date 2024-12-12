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
    ]
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    name = models.CharField(max_length=200)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)  # The department a teacher belongs to
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True)  # Link to Position model
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    region = models.CharField(max_length=200, null=True, blank=True)  # Optional: region or area

    def __str__(self):
        return self.name


# Schedule Model
class Schedule(models.Model):
    CLASS_TYPE_CHOICES = [
        ('Worship', '崇拜'),
        ('Hymn', '詩頌'),
        ('Extra Activity', '共習'),
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
        return f"{self.department.name} - {self.date} ({self.start_time} - {self.end_time})"


# Activity Model
class Activity(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    details = models.TextField(null=True, blank=True)
    class_type = models.CharField(max_length=50, choices=Schedule.CLASS_TYPE_CHOICES)

    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"

    def __str__(self):
        return f"{self.activity_type} for {self.schedule}"


# RoleAssignment Model
class RoleAssignment(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    role = models.CharField(max_length=200)  # Role such as Teacher, Assistant, etc.
    person = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)

    def clean(self):
        """
        Prevent assigning a teacher to multiple tasks that have overlapping time slots.
        """
        if self.person:
            conflicting_assignments = RoleAssignment.objects.filter(
                person=self.person,
                schedule__date=self.schedule.date,
                # Check overlapping time slots
                schedule__start_time__lt=self.schedule.end_time,
                schedule__end_time__gt=self.schedule.start_time
            ).exclude(id=self.id)  # Exclude the current instance being validated

            if conflicting_assignments.exists():
                raise ValidationError(
                    f"{self.person.name} is already assigned to another task "
                    f"from {conflicting_assignments[0].schedule.start_time} to {conflicting_assignments[0].schedule.end_time}."
                )

    def save(self, *args, **kwargs):
        """
        Call the validation method before saving.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.role} - {self.person.name if self.person else 'Unassigned'} for {self.schedule}"