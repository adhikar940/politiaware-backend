from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import District, DistrictMap

admin.site.register(District, ImportExportModelAdmin)
admin.site.register(DistrictMap, admin.GISModelAdmin if hasattr(admin, 'GISModelAdmin') else admin.ModelAdmin)

