from django.urls import path
from .views import (AllSchedulesView, HymnClassesView, PreKindergartenSchedulesView,
                    KindergartenSchedulesView, Elementary1SchedulesView,
                    Elementary1CNJPSchedulesView, Elementary2SchedulesView,
                    JuniorSchedulesView, JuniorJPSchedulesView, PianicaSchedulesView,
                    ShinkoyasuSchedulesView)

urlpatterns = [
    path('schedules/hymn_classes/', HymnClassesView.as_view(), name="hymn_class_schedules"),
    path('schedules/pre_kindergarten/', PreKindergartenSchedulesView.as_view(), name='pre_kindergarten_schedules'),
    path('schedules/kindergarten/', KindergartenSchedulesView.as_view(), name='kindergarten_schedules'),
    path('schedules/elementary1/', Elementary1SchedulesView.as_view(), name='elementary_1_schedules'),
    path('schedules/elementary1_cn_jp/', Elementary1CNJPSchedulesView.as_view(), name='elementary_1_cn_jp_schedules'),
    path('scheudles/elementary2/', Elementary2SchedulesView.as_view(), name='elementary_2_schedules'),
    path('schedules/junior/', JuniorSchedulesView.as_view(), name='junior_schedules'),
    path('schedules/junior_jp/', JuniorJPSchedulesView.as_view(), name='junior_jp_schedules'),
    path('schedules/pianica/', PianicaSchedulesView.as_view(), name='pianica_schedules'),
    path('schedules/shinkoyasu/', ShinkoyasuSchedulesView.as_view(), name='shinkoyasu_schedules'),
    path('schedules/all/', AllSchedulesView.as_view(), name='all_schedules')
]