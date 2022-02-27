from django.conf.urls import url

from . import views

app_name='doser'
urlpatterns = [
    #ex: /doser
    url(r'^(?P<formResult>[\w-]*)$',views.index,name='index'),
    #ex: /doser/home
    url(r'^home/?(?P<formResult>[\w-]*)$',views.home,name='home'),
    #ex: /doser/home
    url(r'^history/?(?P<formResult>[\w-]*)$',views.history,name='history'),
    #ex: /doser/control
    url(r'^control/?(?P<formResult>[\w-]*)$',views.control,name='control'),
    #ex: /doser/calibrate
    url(r'^calibrate/?(?P<formResult>[\w-]*)$',views.calibrate,name='calibrate'),
    #ex: /doser/dosdef
    url(r'^dosedef/?(?P<formResult>[\w-]*)$',views.dosedef,name='dosedef'),
    #ex: /doser/schedule
    url(r'^schedule/?(?P<formResult>[\w-]*)$',views.schedule,name='schedule'),
    #ex: /doser/logs
    url(r'^logs/?(?P<formResult>[\w-]*)$',views.logs,name='logs'),
    #ex: /doser/admin
    url(r'^admin/?(?P<formResult>[\w-]*)$',views.admin,name='admin'),

]