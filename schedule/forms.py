from django.forms.models import BaseInlineFormSet
from .models import Schedule, RoleAssignment

class RoleAssignmentInlineFormset(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        # Extract schedule data from the form
        schedule_data = {
            'date': form.cleaned_data['schedule'].date,
            'start_time': form.cleaned_data['schedule'].start_time,
            'end_time': form.cleaned_data['schedule'].end_time,
            'department': form.cleaned_data['schedule'].department,
        }

        # Check if a schedule with these attributes already exists
        existing_schedule = Schedule.objects.filter(**schedule_data).first()
        if existing_schedule:
            # Reuse the existing schedule
            form.instance.schedule = existing_schedule
        else:
            # Create a new schedule
            schedule = Schedule.objects.create(**schedule_data)
            form.instance.schedule = schedule

        return super().save_new(form, commit)