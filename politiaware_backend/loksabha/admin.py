from django.contrib import admin
from . models import *
from import_export.admin import ImportExportModelAdmin
'''class loksabhaAdmin1(admin.ModelAdmin):
    search_fields = ('MP_name',)
admin.site.register(LokSabha1,loksabhaAdmin1)'''
admin.site.register(LoksabhaConstituency, ImportExportModelAdmin)
admin.site.register(LoksabhaConstituencyMap, admin.GISModelAdmin if hasattr(admin, 'GISModelAdmin') else admin.ModelAdmin)
admin.site.register(LokSabhaMP, ImportExportModelAdmin)
#admin.site.register(Loksabha_Session1, ImportExportModelAdmin)
'''class loksabhapersonalAdmin1(admin.ModelAdmin):
    search_fields = ('mp',)
admin.site.register(loksabhapersonal1, loksabhapersonalAdmin1)'''
#admin.site.register(loksabhapersonal1, ImportExportModelAdmin)
#admin.site.register(Loksabha_Complete_Session1, ImportExportModelAdmin)
