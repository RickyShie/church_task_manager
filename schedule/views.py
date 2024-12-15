from django.views.generic import ListView, TemplateView
from .models import Schedule, Department
from django.http import HttpResponse


class AllSchedulesView(ListView):
    """
    View to display all schedules regardless of department.
    """
    model = Schedule
    template_name = 'schedule/all_schedules.html'
    context_object_name = 'schedules'

    def get_queryset(self):
        return Schedule.objects.all().order_by('date', 'start_time')


# Can I modify the following class so that it can extract records from the Schedule table where class_type = '詩頌課'?
class DepartmentScheduleView(ListView):
    model = Schedule
    template_name = 'schedule/department_schedules.html'  # Reuse your template
    context_object_name = 'schedules'

    def get_queryset(self):
        """
        Filter schedules by department name from the URL.
        """
        department_name = self.kwargs.get('department_name')
        print(f"department_name: {department_name}")
        class_type_filter = self.request.GET.get('class_type')

        if class_type_filter == '詩頌課':
            queryset = Schedule.objects.filter(class_type='詩頌').order_by('date', 'start_time')
            return queryset
        else:
            queryset = Schedule.objects.filter(department__name=department_name).order_by('date', 'start_time')
            return queryset


    def get_context_data(self, **kwargs):
        """
        Add the department name to the context for the template.
        """
        context = super().get_context_data(**kwargs)
        department_name = self.kwargs.get('department_name')
        context['department_name'] = department_name
        return context


from django.shortcuts import render, redirect
from .forms import RoleAssignmentForm

def assign_role(request):
    if request.method == 'POST':
        form = RoleAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('your_success_url')  # Redirect to a success page or reload the current page
    else:
        form = RoleAssignmentForm()

    return render(request, 'schedule/assign_role.html', {'form': form})