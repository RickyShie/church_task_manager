from django.urls import path
from .views import DepartmentScheduleView, AllSchedulesView, HymnClassesView, PreKindergartenSchedulesView

urlpatterns = [
    path('schedules/', AllSchedulesView.as_view(), name='all_schedules'),
    path('schedules/pre_kindergarten/', PreKindergartenSchedulesView.as_view(), name='pre_kindergarten_schedules'),
    # path('schedules/<str:department_name>/', DepartmentScheduleView.as_view(), name='department_schedules'),
    path('schedules/hymn_classes', HymnClassesView.as_view(), name="hymn_class_schedules")
]