from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from charity_donations.models import Institution


class CustomUserAdmin(UserAdmin):
    # Prevention of deleting last superuser
    def delete_model(self, request, obj):
        if obj.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
            raise PermissionDenied(_('You cannot delete the last superuser.'))
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        if queryset.filter(is_superuser=True).count() >= User.objects.filter(is_superuser=True).count():
            raise PermissionDenied(_('You cannot delete the last superuser.'))
        super().delete_queryset(request, queryset)


# Unregister User, and then register it back with CustomUserAdmin deletion prevention functions
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'type_display')  # Customize the list display in the admin panel
    list_filter = ('type', 'categories')  # Filtering by type and categories
    search_fields = ('name', 'description')  # Add search functionality based on name and description

    def type_display(self, obj):
        return obj.get_type_display()

    type_display.short_description = 'Type'


admin.site.register(Institution, InstitutionAdmin)
