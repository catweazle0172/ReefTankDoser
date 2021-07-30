from django.contrib import admin
from django.contrib.admin import AdminSite
# Register your models here.
from django.utils.timezone import get_current_timezone, activate

activate(get_current_timezone())

from .databaseAdmin import *

class ConfigureSite(AdminSite):
    site_header='Configure Site'
    
configure_admin=ConfigureSite(name='configure')