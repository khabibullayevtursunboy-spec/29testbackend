from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "full_name", "role", "school_class", "is_staff")
    list_filter = ("role", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Maktab ma'lumotlari", {"fields": ("role", "full_name", "school_class")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Maktab ma'lumotlari", {"fields": ("role", "full_name", "school_class")}),
    )
