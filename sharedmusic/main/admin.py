from django.contrib import admin
from main.models import Room, CustomUser
from django.contrib.auth.admin import UserAdmin


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Controls which fields are displayed on the change list(!) page of the admin.
    list_display = ('username','email', 'is_staff', 'is_superuser', 'is_active', 'date_joined',)
    # Controls what filters are available
    list_filter = ('is_staff', 'is_active',)
    # When editing user
    fieldsets = (
        ('Information', {'fields': ('email', 'username', 'photo', 'password',)}),
        ('Permissions', {
            'fields': ('is_superuser', 'is_staff', 'is_active', 'user_permissions', 'groups',)
        }),
    )
    # When creating new user via admin dashboard
    add_fieldsets = (
        (
            None,
            {
                # CSS style classes
                'classes': ('wide',),
                'fields': (
                    'email',
                    'username',
                    'photo',
                    'password1',
                    'password2',
                    'is_superuser',
                    'is_staff',
                    'is_active',
                    'user_permissions',
                    'groups',
                )
            }
        ),
    )
    # Search
    search_fields = ('email',)
    # Ordering
    ordering = ('email',)


admin.site.register(Room)
