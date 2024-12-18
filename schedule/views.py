from django.views.generic import ListView, TemplateView
from django.shortcuts import redirect, render
from django.core.exceptions import ValidationError
from .models import Schedule, RoleAssignment, ClassRole, Teacher
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.forms.models import model_to_dict
import pandas as pd

HYMN_CLASS = "詩頌"
WORSHIP_CLASS = "崇拜"
ACTIVITY_CLASS = "共習"
PRE_KINDERGARTEN = "幼幼班"
KINDERGARTEN = "幼稚班"
ELEMENTARY_1 = "幼年班"
ELEMENTARY_1_CN_JP = "幼年班(中日文)"
ELEMENTARY_2 = "少年班"
JUNIOR = "青教組"
JUNIOR_JP = "日文班"
PIANICA = "口風琴班"
SHINKOYASU = "新子安"
ALL_RE_SCHEDULES = "宗教教育總表"



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

# Here is my HymnClassesView.
class HymnClassesView(ListView):
    """
    View to display schedules filtered by department and handle role assignments.
    """
    model = Schedule
    template_name = 'schedule/hymn_class_schedules.html'
    context_object_name = 'schedules'

    def pivot_schedules(self, schedules):
        # Initialize a list to hold rows for the DataFrame
        rows = []

        # Loop through schedules and their role assignments
        for schedule in schedules:
            if not schedule.role_assignments.exists():  # Handle schedules without role assignments
                row = {
                    'date': schedule.date,
                    'department': schedule.department.name,
                    'hymn_type': schedule.hymn_type.name if schedule.hymn_type else '',
                    'hymn_number': schedule.hymn_number,
                    'hymn_topic': schedule.topic,
                    'role': '',
                    'person': '',
                }
                rows.append(row)
            else:
                for role_assignment in schedule.role_assignments.all():
                    row = {
                        'date': schedule.date,
                        'department': schedule.department.name,
                        'hymn_type': schedule.hymn_type.name if schedule.hymn_type else '',
                        'hymn_number': schedule.hymn_number,
                        'hymn_topic': schedule.topic,
                        'role': role_assignment.role.name if role_assignment.role else '',
                        'person': role_assignment.person.name if role_assignment.person else '',
                    }
                    rows.append(row)
        # Check if rows list is empty
        if not rows:
            return pd.DataFrame()  # Return an empty DataFrame

        # Convert the list of rows into a DataFrame
        df = pd.DataFrame(rows)

        # Replace '幼年班(中日文)' with '幼年班' in the 'department' column
        df['department'] = df['department'].replace('幼年班(中日文)', '幼年班')

        if df.empty:  # Handle empty DataFrame case
            return pd.DataFrame()

        # Replace NaN with empty strings.
        df = df.fillna('')

        result = df.pivot_table(
            index=['date', 'department', 'hymn_type', 'hymn_number', 'hymn_topic'],
            columns='role',
            values='person',
            aggfunc='first'  # Use 'first' for non-duplicate roles
        ).reset_index()

        # Flatten MultiIndex columns
        result.columns.name = None
        result = result.rename_axis(None, axis=1)
        return result

    def reshape_dateframe_to_fit_the_template_format(self, df: pd.DataFrame):
        if df.empty:  # Check if DataFrame is empty
            return pd.DataFrame(columns=[
                'date',
                'hymn_type_k', 'hymn_number_k', 'hymn_topic_k', 'teacher_k', 'assistant_k', 'pianist_k', 'department_k',
                'hymn_number_e', 'hymn_topic_e', 'teacher_e', 'pianist_e', 'department_e'
            ])

        # Step 1: Split Data into Two Groups
        kindergarten_df = df[df['department'] == '幼稚班'].copy()
        elementary_df = df[df['department'].isin(['幼年班', '幼年班(中日文)', '少年班'])].copy()

        # Step 2: Rename Columns to Distinguish Groups
        kindergarten_df = kindergarten_df.rename(columns={
            'hymn_type': 'hymn_type_k',
            'hymn_number': 'hymn_number_k',
            'hymn_topic': 'hymn_topic_k',
            '主領': 'teacher_k',
            '助教': 'assistant_k',
            '司琴': 'pianist_k',
            'department': 'department_k'
        })

        elementary_df = elementary_df.rename(columns={
            'hymn_type': 'hymn_type_e',
            'hymn_number': 'hymn_number_e',
            'hymn_topic': 'hymn_topic_e',
            '主領': 'teacher_e',
            '助教': 'assistant_e',
            '司琴': 'pianist_e',
            'department': 'department_e'
        })

        # Step 3: Merge the Two Groups on 'date'
        merged_df = pd.merge(kindergarten_df, elementary_df, on='date', how='outer')

        # Step 4: Rearrange Columns for Final Output
        final_columns = [
            'date',
            'hymn_type_k', 'hymn_number_k', 'hymn_topic_k', 'teacher_k', 'assistant_k', 'pianist_k', 'department_k',
            'hymn_number_e', 'hymn_topic_e', 'teacher_e', 'pianist_e', 'department_e'
        ]
        final_df = merged_df.reindex(columns=final_columns, fill_value=None)

        # Replace NaN values with empty strings
        final_df = final_df.fillna('')
        return final_df

    def get_queryset(self):

        """
        Process and group hymn class schedules into a list of dictionaries
        containing relevant details.
        """
        # Fetch schedules with related RoleAssignments, Roles, and Persons
        hymn_schedules = Schedule.objects.filter(
            class_type=HYMN_CLASS
        ).prefetch_related('role_assignments__role', 'role_assignments__person')

        pivoted_schedules = self.pivot_schedules(hymn_schedules)
        reformatted_df = self.reshape_dateframe_to_fit_the_template_format(pivoted_schedules)

        # Convert DataFrame to list of dictionaries
        reformatted_list = reformatted_df.to_dict(orient='records')
        return reformatted_list


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
                url = f"{reverse('hymn_class_schedules')}?error={error_message}"
                return HttpResponseRedirect(url)
            else:
                # Redirect back to the department schedules page
                return redirect('hymn_class_schedules')

    def get_context_data(self, **kwargs):
        """
        Pass two separate querysets for different department groups to the template.
        """
        context = super().get_context_data(**kwargs)
        context['hymn_schedules'] = self.get_queryset()
        context['schedules'] = Schedule.objects.filter(class_type=HYMN_CLASS).order_by('date')

        # Definal the specific class roles you want to include in the dropdown.
        allowed_roles = ['主領', '司琴', '助教']
        context['roles'] = ClassRole.objects.filter(name__in=allowed_roles)
        context['persons'] = Teacher.objects.all()

        return context



class PreKindergartenSchedulesView(TemplateView):
    """
    A custom view for rendering schedules and role assignments in a format suitable for pre_kindergarten classes.
    """
    template_name = 'schedule/pre_kindergarten_schedules.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filter and sort schedules for '崇拜' (Worship Class)
        worship_schedules = Schedule.objects.filter(
            class_type=WORSHIP_CLASS,
            department__name=PRE_KINDERGARTEN
        ).order_by('date').values('date', 'topic')

        # Filter and sort role assignments for '崇拜' (Teacher Role)
        worship_teachers = RoleAssignment.objects.filter(
            schedule__class_type=WORSHIP_CLASS,
            schedule__department__name=PRE_KINDERGARTEN,
            role__name='講師'
        ).order_by('schedule__date').values('schedule__date', 'person__name')

        # Filter and sort schedules for '共習' (Activity Class)
        activity_schedules = Schedule.objects.filter(
            class_type=ACTIVITY_CLASS,
            department__name=PRE_KINDERGARTEN
        ).order_by('date').values('date', 'topic')

        # Filter and sort role assignments for '共習' (Assistant Role)
        activity_assistants = RoleAssignment.objects.filter(
            schedule__class_type=ACTIVITY_CLASS,
            schedule__department__name=PRE_KINDERGARTEN,
            role__name='助教'
        ).order_by('schedule__date').values('schedule__date', 'person__name')
        print(f"activity_assitants: \n\n{activity_assistants}\n\n")

        # Organize data into the context
        context['worship_schedules'] = worship_schedules
        context['worship_teachers'] = worship_teachers
        context['activity_schedules'] = activity_schedules
        context['activity_assistants'] = activity_assistants
        return context