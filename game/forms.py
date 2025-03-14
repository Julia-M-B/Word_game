from django import forms

from .models import Game, Player


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ["nickname"]


class GameForm(forms.ModelForm):
    word = forms.CharField(label="Word", max_length=200)

    # category = forms.CharField(label='Game category', max_length=200)
    class Meta:
        model = Game
        fields = ["word"]
