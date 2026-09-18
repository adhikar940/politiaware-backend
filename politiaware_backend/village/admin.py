from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Village, VillageMap

admin.site.register(Village, ImportExportModelAdmin)
admin.site.register(VillageMap, admin.GISModelAdmin if hasattr(admin, 'GISModelAdmin') else admin.ModelAdmin)

