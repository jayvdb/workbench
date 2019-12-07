from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from workbench.accounts.models import User
from workbench.awt.models import Employment


class UserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "_short_name", "_full_name", "is_active", "is_admin")


class EmploymentInline(admin.TabularInline):
    model = Employment
    extra = 0


class UserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserChangeForm

    list_display = (
        "email",
        "_short_name",
        "_full_name",
        "is_active",
        "is_admin",
        "enforce_same_week_logging",
        "last_login",
    )
    list_filter = ("is_active", "is_admin")
    fieldsets = add_fieldsets = [
        (
            None,
            {
                "fields": [
                    field.name
                    for field in User._meta.get_fields()
                    if field.editable and field.name not in {"password", "id"}
                ]
            },
        )
    ]
    search_fields = ("email", "_short_name", "_full_name")
    ordering = ("email",)
    filter_horizontal = ()
    inlines = [EmploymentInline]


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)  # We are not using stock users or groups.
