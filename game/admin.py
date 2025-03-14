from django.contrib import admin

from . import models

# Register your models here.
admin.site.register(models.Player)


class GameAdmin(admin.ModelAdmin):
    ordering = [
        "-created",
    ]
    pass


admin.site.register(models.Game, GameAdmin)
