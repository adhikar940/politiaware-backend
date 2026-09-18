from django.contrib import admin
from import_export.admin import ImportExportModelAdmin,ImportExportActionModelAdmin
from . models import *
from import_export import resources
'''class Party1Resource(resources.ModelResource):
    class Meta:
        model = Party
class Party1Admin(ImportExportModelAdmin):
    list_display=('id','abbreviation')
    search_fields = ['partyname','abbreviation']
    resource_class = Party1Resource
admin.site.register(Party, Party1Admin)'''
admin.site.register(Party, ImportExportModelAdmin)
#admin.site.register(statepartyactivate1, ImportExportModelAdmin)
#admin.site.register(districtpartyactivate1, ImportExportModelAdmin)
