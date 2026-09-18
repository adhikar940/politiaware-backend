from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import State, StateMap, area, population

admin.site.register(State, ImportExportModelAdmin)
admin.site.register(StateMap, admin.GISModelAdmin if hasattr(admin, 'GISModelAdmin') else admin.ModelAdmin)
admin.site.register(area, ImportExportModelAdmin)
admin.site.register(population, ImportExportModelAdmin)

