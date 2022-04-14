from django.db import models


class Room(models.Model):
    code = models.CharField(max_length=120, unique=True, verbose_name="Code")
    #slug = models.SlugField(max_length=120, unique=True, verbose_name="Slug")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation date")

    class Meta:
        verbose_name_plural = "Rooms"
        verbose_name = "Room"
        ordering = ["-id"]
