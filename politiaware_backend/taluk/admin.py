from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Taluk, TalukMap

admin.site.register(Taluk, ImportExportModelAdmin)
admin.site.register(TalukMap, admin.GISModelAdmin if hasattr(admin, 'GISModelAdmin') else admin.ModelAdmin)

