from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import City, CityMap

admin.site.register(City, ImportExportModelAdmin)
admin.site.register(CityMap, admin.GISModelAdmin if hasattr(admin, 'GISModelAdmin') else admin.ModelAdmin)

