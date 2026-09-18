from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Panchayat, PanchayatMap

admin.site.register(Panchayat, ImportExportModelAdmin)
admin.site.register(PanchayatMap, admin.GISModelAdmin if hasattr(admin, 'GISModelAdmin') else admin.ModelAdmin)

