from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Counselor, Student, Parent


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_student', 'is_counselor', 'is_parent', 'is_staff')
    list_filter = UserAdmin.list_filter + ('is_student', 'is_counselor', 'is_parent')
    fieldsets = UserAdmin.fieldsets + (
        ('Rehberim', {'fields': ('is_student', 'is_counselor', 'is_parent')}),
    )


@admin.register(Counselor)
class CounselorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'invite_code')
    readonly_fields = ('invite_code',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'grade', 'study_field', 'counselor', 'connect_code')
    list_filter = ('grade', 'study_field')
    readonly_fields = ('connect_code',)


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user')
    filter_horizontal = ('students',)
