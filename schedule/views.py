from django.views.generic import ListView
from django.shortcuts import redirect, render
from django.core.exceptions import ValidationError
from .models import Schedule, RoleAssignment, ClassRole, Teacher
from django.urls import reverse
from django.http import HttpResponseRedirect


class AllSchedulesView(ListView):
    """
    View to display all schedules regardless of department and handle role assignments.
    """
    model = Schedule
    template_name = 'schedule/all_schedules.html'
    context_object_name = 'schedules'

    def get_queryset(self):
        return Schedule.objects.all().order_by('date', 'start_time')

    def post(self, request, *args, **kwargs):
        # Handle role assignment here
        schedule_id = request.POST.get('schedule')
        role_id = request.POST.get('role')
        person_id = request.POST.get('person')

        if schedule_id and role_id and person_id:
            schedule = Schedule.objects.get(id=schedule_id)
            role = ClassRole.objects.get(id=role_id)
            person = Teacher.objects.get(id=person_id)

            # Create the RoleAssignment object
            RoleAssignment.objects.create(schedule=schedule, role=role, person=person)

        return redirect('all_schedules')  # Redirect to refresh the page


class DepartmentScheduleView(ListView):
    """
    View to display schedules filtered by department and handle role assignments.
    """
    model = Schedule
    template_name = 'schedule/department_schedules.html'
    context_object_name = 'schedules'

    def get_queryset(self):
        department_name = self.kwargs.get('department_name')
        class_type_filter = self.request.GET.get('class_type')

        if class_type_filter == '詩頌課':
            return Schedule.objects.filter(class_type='詩頌').order_by('date', 'start_time')
        else:
            return Schedule.objects.filter(department__name=department_name).order_by('date', 'start_time')

    def post(self, request, *args, **kwargs):
        schedule_id = request.POST.get('schedule')
        role_id = request.POST.get('role')
        person_id = request.POST.get('person')

        if schedule_id and role_id and person_id:
            schedule = Schedule.objects.get(id=schedule_id)
            role = ClassRole.objects.get(id=role_id)
            person = Teacher.objects.get(id=person_id)

            try:
                # Create the RoleAssignment object
                RoleAssignment.objects.create(schedule=schedule, role=role, person=person)
            except ValidationError as e:
                # Redirect with an error message as a query parameter
                error_message = str(e)
                department_name = self.kwargs.get('department_name')
                url = f"{reverse('department_schedules', kwargs={'department_name': department_name})}?error={error_message}"
                return HttpResponseRedirect(url)
            else:
                # Redirect back to the department schedules page
                return redirect('department_schedules', department_name=self.kwargs.get('department_name'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        department_name = self.kwargs.get('department_name')

        # Add dropdown data
        context['schedules'] = Schedule.objects.filter(department__name=department_name)
        context['roles'] = ClassRole.objects.all()
        context['persons'] = Teacher.objects.all()
        context['department_name'] = department_name

        return context