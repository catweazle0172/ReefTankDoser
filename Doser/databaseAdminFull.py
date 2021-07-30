from django.contrib import admin

from .models import DoserExternal,DoseDefinition,DoseSchedule,JobExternal,DoseResultsExternal

admin.site.register(DoserExternal)
admin.site.register(DoseDefinition)
admin.site.register(DoseSchedule)
admin.site.register(JobExternal)
admin.site.register(DoseResultsExternal)