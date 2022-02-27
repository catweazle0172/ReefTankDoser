from django.urls import re_path

from . import views

app_name='doser'
urlpatterns = [
    #ex: /doser
    re_path(r'^(?P<formResult>[\w-]*)$',views.index,name='index'),
    #ex: /doser/home
    re_path(r'^home/?(?P<formResult>[\w-]*)$',views.home,name='home'),
    #ex: /doser/home
    re_path(r'^history/?(?P<formResult>[\w-]*)$',views.history,name='history'),
    #ex: /doser/control
    re_path(r'^control/?(?P<formResult>[\w-]*)$',views.control,name='control'),
    #ex: /doser/calibrate
    re_path(r'^calibrate/?(?P<formResult>[\w-]*)$',views.calibrate,name='calibrate'),
    #ex: /doser/dosdef
    re_path(r'^dosedef/?(?P<formResult>[\w-]*)$',views.dosedef,name='dosedef'),
    #ex: /doser/schedule
    re_path(r'^schedule/?(?P<formResult>[\w-]*)$',views.schedule,name='schedule'),
    #ex: /doser/logs
    re_path(r'^logs/?(?P<formResult>[\w-]*)$',views.logs,name='logs'),
    #ex: /doser/admin
    re_path(r'^admin/?(?P<formResult>[\w-]*)$',views.admin,name='admin'),
]
