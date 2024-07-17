from django.contrib import admin
from charity_donations.models import Institution


class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'type_display')  # Customize the list display in the admin panel
    list_filter = ('type', 'categories')  # Filtering by type and categories
    search_fields = ('name', 'description')  # Add search functionality based on name and description

    def type_display(self, obj):
        return obj.get_type_display()
    type_display.short_description = 'Type'


admin.site.register(Institution, InstitutionAdmin)
