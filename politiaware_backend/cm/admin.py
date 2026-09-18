from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import cm

admin.site.register(cm, ImportExportModelAdmin)
