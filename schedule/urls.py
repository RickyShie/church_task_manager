from django.urls import path
from .views import DepartmentScheduleView, AllSchedulesView

urlpatterns = [
    path('schedules/', AllSchedulesView.as_view(), name='all_schedules'),
    path('schedules/<str:department_name>/', DepartmentScheduleView.as_view(), name='department_schedules')
]