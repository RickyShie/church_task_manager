from django.views.generic import ListView, TemplateView
from django.shortcuts import redirect, render
from django.core.exceptions import ValidationError
from .models import Schedule, RoleAssignment, ClassRole, Teacher
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.forms.models import model_to_dict
import pandas as pd
from functools import reduce

pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 500)

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


def merge_querysets_by_date(dataframes):
    """
    Merges a list of DataFrames on the 'date' column. Skips DataFrames that do not have a 'date' column.

    :param dataframes: A list of Pandas DataFrames
    :return: A merged DataFrame
    """
    # Filter DataFrames to include only those with a 'date' column
    valid_dataframes = [df for df in dataframes if 'date' in df.columns]

    if not valid_dataframes:
        raise ValueError("No DataFrames with a 'date' column were provided.")

    # Merge the valid DataFrames on the 'date' column
    result = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), valid_dataframes)
    return result


def get_role_assignments(class_type, department_name, role_name, column_name, value_field='person__name'):
    """
    Fetches role assignments filtered by class type, department, and role,
    and returns a DataFrame with renamed columns.

    :param class_type: The class type (single value or list of values) to filter (e.g., WORSHIP_CLASS or ['詩頌', '共習'])
    :param department_name: The name of the department to filter (e.g., KINDERGARTEN)
    :param role_name: The name of the role to filter (e.g., '老師', '司琴', etc.)
    :param column_name: The new column name for the extracted value
    :param value_field: The field to retrieve as value (default: 'person__name')
    :return: A DataFrame with date and the specified value field
    """
    filter_kwargs = {
        'schedule__department__name': department_name,
        'role__name': role_name
    }

    # Handle single or multiple class types
    if isinstance(class_type, list):
        filter_kwargs['schedule__class_type__in'] = class_type
    else:
        filter_kwargs['schedule__class_type'] = class_type

    role_assignments = RoleAssignment.objects.filter(
        **filter_kwargs
    ).order_by('schedule__date').values('schedule__date', value_field)

    result_df = pd.DataFrame(role_assignments).rename(columns={'schedule__date': 'date', value_field: column_name})

    return result_df


def get_schedule_topics(class_types, department_name, column_name, include_hymn_number=False, include_unit_number=False):
    """
    Fetches schedules filtered by class type(s) and department and returns a DataFrame with renamed columns.

    :param class_types: A single class type or a list of class types to filter (e.g., WORSHIP_CLASS, ACTIVITY_CLASS, or ['詩頌', '共習'])
    :param department_name: The name of the department to filter (e.g., PRE_KINDERGARTEN)
    :param column_name: The new column name for the topic
    :param include_hymn_number: Whether to include hymn_number in the DataFrame
    :param unit_number_column_name: The new column name for the unit_number field (optional)
    :return: A DataFrame with date, topic, hymn_number, and optionally unit_number columns
    """
    filter_kwargs = {
        'department__name': department_name
    }

    # Handle single or multiple class types
    if isinstance(class_types, list):
        filter_kwargs['class_type__in'] = class_types
    else:
        filter_kwargs['class_type'] = class_types

    # Fetch schedules
    schedules = Schedule.objects.filter(**filter_kwargs).order_by('date').values('date', 'topic', 'hymn_number', 'unit_number')
    df = pd.DataFrame(schedules).rename(columns={'topic': column_name})

    # Replace NaN with an empty string for hymn_number
    df['hymn_number'] = df['hymn_number'].fillna('')

    # Convert numeric values in hymn_number to integers where possible
    df['hymn_number'] = df['hymn_number'].apply(
        lambda x: int(x) if isinstance(x, float) and not pd.isnull(x) else x
    )

    # Rename the unit_number column if a new name is provided
    if not include_unit_number:
        df = df.drop(columns=['unit_number'], errors='ignore')

    # Remove hymn_number column if include_hymn_number is False
    if not include_hymn_number:
        df = df.drop(columns=['hymn_number'], errors='ignore')

    return df


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

        # Fetch schedules and convert them to DataFrames
        worship_topic_df = get_schedule_topics(WORSHIP_CLASS, PRE_KINDERGARTEN, 'worship_topic')
        activity_topic_df = get_schedule_topics(ACTIVITY_CLASS, PRE_KINDERGARTEN, 'activity_topic')

        # Fetch role assignments and convert them to DataFrames
        worship_teachers_df = get_role_assignments(WORSHIP_CLASS, PRE_KINDERGARTEN, '講師', 'worship_teacher')
        activity_assistant1_df = get_role_assignments(ACTIVITY_CLASS, PRE_KINDERGARTEN, '助教1', 'assistant_1')
        activity_assistant2_df = get_role_assignments(ACTIVITY_CLASS, PRE_KINDERGARTEN, '助教2', 'assistant_2')

        result_df = merge_querysets_by_date([worship_topic_df, worship_teachers_df,
                                             activity_topic_df, activity_assistant1_df, activity_assistant2_df])
        context['pre_kindergarten_schedules'] = result_df.to_dict(orient='records')
        return context


class KindergartenSchedulesView(TemplateView):
    """
    A custom view for rendering schedules and role assignments in a format suitable for kindergarten classes.
    """
    template_name = 'schedule/kindergarten_schedules.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch schedules and convert them to DataFrames
        hymn_topic_df = get_schedule_topics(HYMN_CLASS, KINDERGARTEN, 'hymn_topic', include_hymn_number=True)
        worship_topic_df = get_schedule_topics(WORSHIP_CLASS, KINDERGARTEN, 'worship_topic', False, True)
        # Drop hymn_number column from worship_topic_df DataFrame.
        activity_topic_df = get_schedule_topics(ACTIVITY_CLASS, KINDERGARTEN, 'activity_topic')

        # Fetch role assignments and convert them to DataFrames
        hymn_teachers_df = get_role_assignments(HYMN_CLASS, KINDERGARTEN, '老師', 'hymn_teacher')
        hymn_pianists_df = get_role_assignments(HYMN_CLASS, KINDERGARTEN, '司琴', 'hymn_pianist')
        hymn_assistants_df = get_role_assignments(HYMN_CLASS, KINDERGARTEN, '助教1', 'hymn_assistant')
        worship_teachers_df = get_role_assignments(WORSHIP_CLASS, KINDERGARTEN, '老師', 'worship_teacher')
        activity_assistants_df = get_role_assignments(ACTIVITY_CLASS, KINDERGARTEN, '助教1', 'activity_assistant')

        result_df = merge_querysets_by_date([hymn_topic_df, hymn_teachers_df, hymn_pianists_df, hymn_assistants_df,
                                             worship_topic_df, worship_teachers_df,
                                             activity_topic_df, activity_assistants_df])
        context['kindergarten_schedules'] = result_df.to_dict(orient='records')
        return context

class Elementary1SchedulesView(TemplateView):

    template_name = 'schedule/elementary_1_schedules.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch schedules and convert them to DataFrames
        worship_topic_df = get_schedule_topics(WORSHIP_CLASS, ELEMENTARY_1, 'worship_topic', include_hymn_number=True, include_unit_number=True)
        worship_topic_df.rename(columns={'hymn_number': 'worship_hymn_number'}, inplace=True)
        hymn_activity_topic_df = get_schedule_topics(class_types=[HYMN_CLASS, ACTIVITY_CLASS], department_name=ELEMENTARY_1, column_name='hymn_activity_topic', include_hymn_number=True)
        hymn_activity_topic_df.rename(columns={'hymn_number': 'hymn_hymn_number'}, inplace=True)

        hymn_activity_class_types_df = get_role_assignments(class_type=[HYMN_CLASS, ACTIVITY_CLASS], department_name=ELEMENTARY_1, role_name='講師', column_name='class_type', value_field='schedule__class_type')

        # Fetch role assignments and convert them to DataFrames
        worship_teachers_df = get_role_assignments(WORSHIP_CLASS, ELEMENTARY_1, '講師', 'worship_teacher')
        worship_assistants_df = get_role_assignments(WORSHIP_CLASS, ELEMENTARY_1, '助教1', 'worship_assistant')
        worship_disciplinarians_df = get_role_assignments(WORSHIP_CLASS, ELEMENTARY_1, '秩序管理', 'worship_disciplinarian')
        worship_pianists_df = get_role_assignments(WORSHIP_CLASS, ELEMENTARY_1, '司琴', 'worship_pianist')
        hymn_activity_teachers_df = get_role_assignments(class_type=[HYMN_CLASS, ACTIVITY_CLASS], department_name=ELEMENTARY_1, role_name='講師', column_name='hymn_acitivity_teacher')
        hymn_activity_pianists_df = get_role_assignments(class_type=[HYMN_CLASS, ACTIVITY_CLASS], department_name=ELEMENTARY_1, role_name='司琴', column_name='hymn_activity_pianist')

        result_df = merge_querysets_by_date([worship_topic_df, worship_teachers_df, worship_assistants_df, worship_disciplinarians_df, worship_pianists_df,
                                             hymn_activity_class_types_df, hymn_activity_topic_df, hymn_activity_teachers_df, hymn_activity_pianists_df])

        # Replace NaN with empty strings.
        result_df.fillna('', inplace=True)

        context['elementary1_schedules'] = result_df.to_dict(orient='records')
        return context


class Elementary1CNJPSchedulesView(TemplateView):

    template_name = 'schedule/elementary_1_cn_jp_schedules.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch schedules and convert them to DataFrames
        worship_topic_df = get_schedule_topics(WORSHIP_CLASS, ELEMENTARY_1_CN_JP, 'worship_topic', include_hymn_number=True, include_unit_number=True)
        worship_topic_df.rename(columns={'hymn_number': 'worship_hymn_number'}, inplace=True)
        hymn_activity_topic_df = get_schedule_topics(class_types=[HYMN_CLASS, ACTIVITY_CLASS], department_name=ELEMENTARY_1_CN_JP, column_name='hymn_activity_topic', include_hymn_number=True)
        hymn_activity_topic_df.rename(columns={'hymn_number': 'hymn_hymn_number'}, inplace=True)

        hymn_activity_class_types_df = get_role_assignments(class_type=[HYMN_CLASS, ACTIVITY_CLASS], department_name=ELEMENTARY_1_CN_JP, role_name='講師', column_name='class_type', value_field='schedule__class_type')

        # Fetch role assignments and convert them to DataFrames
        worship_teachers_df = get_role_assignments(WORSHIP_CLASS, ELEMENTARY_1_CN_JP, '講師', 'worship_teacher')
        worship_assistants_df = get_role_assignments(WORSHIP_CLASS, ELEMENTARY_1_CN_JP, '助教1', 'worship_assistant')
        worship_disciplinarians_df = get_role_assignments(WORSHIP_CLASS, ELEMENTARY_1_CN_JP, '秩序管理', 'worship_disciplinarian')
        worship_pianists_df = get_role_assignments(WORSHIP_CLASS, ELEMENTARY_1_CN_JP, '司琴', 'worship_pianist')
        hymn_activity_teachers_df = get_role_assignments(class_type=[HYMN_CLASS, ACTIVITY_CLASS], department_name=ELEMENTARY_1_CN_JP, role_name='講師', column_name='hymn_acitivity_teacher')
        hymn_activity_pianists_df = get_role_assignments(class_type=[HYMN_CLASS, ACTIVITY_CLASS], department_name=ELEMENTARY_1_CN_JP, role_name='司琴', column_name='hymn_activity_pianist')

        result_df = merge_querysets_by_date([worship_topic_df, worship_teachers_df, worship_assistants_df, worship_disciplinarians_df, worship_pianists_df,
                                             hymn_activity_class_types_df, hymn_activity_topic_df, hymn_activity_teachers_df, hymn_activity_pianists_df])

        # Replace NaN with empty strings.
        result_df.fillna('', inplace=True)

        context['elementary1_schedules'] = result_df.to_dict(orient='records')
        return context


class Elementary2SchedulesView(TemplateView):

    template_name = 'schedule/elementary_2_schedules.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch schedules and convert them to DataFrames
        worship_topic_df = get_schedule_topics(WORSHIP_CLASS, ELEMENTARY_2, 'worship_topic', include_hymn_number=True, include_unit_number=True)
        worship_topic_df.rename(columns={'hymn_number': 'worship_hymn_number'}, inplace=True)
        hymn_activity_topic_df = get_schedule_topics(class_types=[HYMN_CLASS, ACTIVITY_CLASS], department_name=ELEMENTARY_2, column_name='hymn_activity_topic')

        hymn_activity_class_types_df = get_role_assignments(class_type=[HYMN_CLASS, ACTIVITY_CLASS], department_name=ELEMENTARY_2, role_name='講師', column_name='class_type', value_field='schedule__class_type')

        # Fetch role assignments and convert them to DataFrames
        worship_teachers_df = get_role_assignments(WORSHIP_CLASS, ELEMENTARY_2, '講師', 'worship_teacher')
        worship_assistants_df = get_role_assignments(WORSHIP_CLASS, ELEMENTARY_2, '助教1', 'worship_assistant')
        worship_disciplinarians_df = get_role_assignments(WORSHIP_CLASS, ELEMENTARY_2, '秩序管理', 'worship_disciplinarian')
        hymn_activity_teachers_df = get_role_assignments(class_type=[HYMN_CLASS, ACTIVITY_CLASS], department_name=ELEMENTARY_2, role_name='講師', column_name='hymn_activity_teacher')
        hymn_activity_pianists_df = get_role_assignments(class_type=[HYMN_CLASS, ACTIVITY_CLASS], department_name=ELEMENTARY_2, role_name='司琴', column_name='hymn_activity_pianist')

        result_df = merge_querysets_by_date([worship_topic_df, worship_teachers_df, worship_assistants_df, worship_disciplinarians_df,
                                             hymn_activity_class_types_df, hymn_activity_topic_df, hymn_activity_teachers_df, hymn_activity_pianists_df])

        # Replace NaN with empty strings.
        result_df.fillna('', inplace=True)

        context['elementary2_schedules'] = result_df.to_dict(orient='records')
        return context


class JuniorSchedulesView(TemplateView):

    template_name = 'schedule/junior_schedules.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch schedules and convert them to DataFrames
        worship_topic_df = get_schedule_topics(WORSHIP_CLASS, JUNIOR, 'worship_topic', include_hymn_number=True, include_unit_number=True)
        worship_topic_df.rename(columns={'hymn_number': 'worship_hymn_number'}, inplace=True)

        activity_topic_df = get_schedule_topics(class_types=ACTIVITY_CLASS, department_name=JUNIOR, column_name='activity_topic')

        # Fetch role assignments and convert them to DataFrames
        worship_teachers_df = get_role_assignments(WORSHIP_CLASS, JUNIOR, '講師', 'worship_teacher')
        worship_assistants_df = get_role_assignments(WORSHIP_CLASS, JUNIOR, '助教1', 'worship_assistant')
        worship_pianists_df = get_role_assignments(WORSHIP_CLASS, JUNIOR, '司琴', 'worship_pianist')
        activity_teachers_df = get_role_assignments(class_type=[HYMN_CLASS, ACTIVITY_CLASS], department_name=JUNIOR, role_name='講師', column_name='activity_teacher')

        result_df = merge_querysets_by_date([worship_topic_df, worship_teachers_df, worship_assistants_df, worship_pianists_df,
                                             activity_topic_df, activity_teachers_df])
        # Replace NaN with empty strings.
        result_df.fillna('', inplace=True)

        context['junior_schedules'] = result_df.to_dict(orient='records')
        return context


class JuniorJPSchedulesView(TemplateView):

    template_name = 'schedule/junior_jp_schedules.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

class PianicaSchedulesView(TemplateView):

    template_name = 'schedule/pianica_schedules.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)


class ShinkoyasuSchedulesView(TemplateView):

    template_name = 'schedule/shinkoyasu_schedules.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)