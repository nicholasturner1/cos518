from django.contrib import admin
from mail.models import *

class PersonAdmin(admin.ModelAdmin):
    list_filter = ('is_merged',)
    prepopulated_fields = {"slug": ("name",)}


class EmailAdmin(admin.ModelAdmin):
    
    def _restrict_to_merged(self, db_field, request, **kwargs):
        print db_field.name
        if db_field.name in ('to', 'cc', 'creator'):
            kwargs["queryset"] = Person.objects.filter(merged_into=None)

        return super(EmailAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return self._restrict_to_merged(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        return self._restrict_to_merged(db_field, request, **kwargs)

    
    
class ThreadAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    
    
admin.site.register(Person, PersonAdmin)
admin.site.register(Box)
admin.site.register(Email, EmailAdmin)
admin.site.register(Thread, ThreadAdmin)