from django.contrib import admin
from main.models import Room, CustomUser, Soundtrack, RoomPlaylist, RoomPlaylistTrack, ChatMessage, \
    UserPlaylist
from django.contrib.auth.admin import UserAdmin


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Controls which fields are displayed on the change list(!) page of the admin.
    list_display = ('username', 'email', 'is_staff', 'is_superuser', 'is_active', 'date_joined',)
    # Controls what filters are available
    list_filter = ('is_staff', 'is_active',)
    # When editing user
    fieldsets = (
        ('Information', {'fields': ('email', 'username', 'password', )}),
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


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    model = Room
    list_display = ('id', 'host', 'max_connections', 'last_visited', 'is_deleted', 'creation_date',)
    list_filter = ('is_deleted',)
    search_fields = ('id',)
    ordering = ('creation_date',)


@admin.register(Soundtrack)
class SoundtrackAdmin(admin.ModelAdmin):
    model = Soundtrack
    list_display = ('name', 'id', 'url', 'creation_date',)
    search_fields = ('name', 'id', 'url',)
    ordering = ('creation_date',)


@admin.register(RoomPlaylist)
class RoomPlaylistAdmin(admin.ModelAdmin):
    model = RoomPlaylist
    list_display = ('name', 'room_id', 'room', 'creation_date',)
    search_fields = ('room_id', 'name',)
    ordering = ('creation_date',)


@admin.register(RoomPlaylistTrack)
class RoomPlaylistTrackAdmin(admin.ModelAdmin):
    model = RoomPlaylistTrack
    list_display = ('track', 'playlist', 'id',)
    search_fields = ('id',)
    ordering = ('id',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    model = ChatMessage
    list_display = ('sender', 'room', 'message', 'id', 'timestamp',)
    list_filter = ('sender',)
    search_fields = ('message', 'sender', 'room')
    ordering = ('timestamp',)


@admin.register(UserPlaylist)
class UserPlaylistAdmin(admin.ModelAdmin):
    model = UserPlaylist
    list_display = ('name', 'id', 'user', 'creation_date',)
    search_fields = ('id', 'name')
    ordering = ('creation_date',)
