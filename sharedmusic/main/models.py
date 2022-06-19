import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from main import consts


username_validator = UnicodeUsernameValidator()


class CustomUser(AbstractUser):

    username = models.CharField(
        _('username'),
        max_length=20,
        unique=True,
        help_text=_('Required. 20 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    def __str__(self):
        return self.username


class Soundtrack(models.Model):
    name = models.CharField(default="Soundtrack", max_length=120, verbose_name="Name")
    url = models.URLField(max_length=2000, verbose_name="URL")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation date")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Soundtracks'
        verbose_name = 'Soundtrack'
        ordering = ['-id']


class Playlist(models.Model):
    name = models.CharField(default="Playlist", max_length=120, verbose_name="Name")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation date")

    def __str__(self):
        return f"{self.name}"

    class Meta:
        abstract = True


def permissions_jsonfield_default():
    return dict([
            (consts.CHANGE_TRACK_EVENT, consts.ROOM_ALLOW_ANY),
            (consts.CHANGE_TIME_EVENT, consts.ROOM_ALLOW_ANY),
            (consts.ADD_TRACK_EVENT, consts.ROOM_ALLOW_ANY),
            (consts.DELETE_TRACK_EVENT, consts.ROOM_ALLOW_ANY),
            (consts.PAUSE_TRACK_EVENT, consts.ROOM_ALLOW_ANY),
        ])


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="host", verbose_name="Host")
    listeners = models.ManyToManyField(get_user_model(), blank=True, related_name="listeners", verbose_name="Listeners")
    creation_date = models.DateTimeField(verbose_name="Creation date")
    last_visited = models.DateTimeField(verbose_name="Last visited")
    permissions = models.JSONField(default=permissions_jsonfield_default, verbose_name="Permissions")
    mute_list = models.ManyToManyField(get_user_model(), blank=True, related_name="mute_list", verbose_name="Mute list")
    max_connections = models.IntegerField(default=20, verbose_name="Max connections")
    ban_list = models.ManyToManyField(get_user_model(), blank=True, related_name="ban_list", verbose_name="Ban list")
    is_deleted = models.BooleanField(default=False, verbose_name="Is deleted")

    def __str__(self):
        return f"{self.host}'s room ({self.id})"

    def save(self, *args, **kwargs):
        date = timezone.now()
        if self.creation_date is None:
            self.creation_date = date
        self.last_visited = date
        super(Room, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Rooms"
        verbose_name = "Room"
        ordering = ["-id"]


class ChatMessage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages", verbose_name="Room")
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Sender")
    message = models.CharField(max_length=600, verbose_name="Message")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")


class UserPlaylist(Playlist):
    """
    Represents user playlist. Each user may have more than 1 playlist.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="User")


class RoomPlaylist(Playlist):
    """
    Room playlist. Each room may have only 1 playlist at a time.
    """
    room = models.OneToOneField(
        Room,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="playlist",
        verbose_name="Room"
    )

    def __str__(self):
        return f"{self.name} ({self.room_id})"


class RoomPlaylistTrack(models.Model):
    """
    Represents track in current playlist.
    """
    track = models.ForeignKey(Soundtrack, on_delete=models.CASCADE, verbose_name="Soundtrack")
    playlist = models.ForeignKey(
        RoomPlaylist,
        on_delete=models.CASCADE,
        related_name='tracks',
        verbose_name="Room playlist"
    )

    class Meta:
        verbose_name_plural = 'Room playlist tracks'
        verbose_name = 'Room playlist track'
        ordering = ['-id']
