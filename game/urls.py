from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("new-game/", views.new_game, name="new-game"),
    path("game/<str:pk>/", views.game, name="game"),
    path("my-games/", views.my_games, name="my-games"),
    path("game/<str:pk>/status", views.game_status, name="game-status"),
    path("game/<str:pk>/answer", views.answer, name="answer"),
    path("invite/<str:pk>/", views.join_game, name="invite"),
    path("new-player/", views.new_player, name="new-player"),
]
