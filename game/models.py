import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q


class Game(models.Model):
    WAITING_FOR_GUEST = "waiting for player to join"
    WAITING_FOR_HOST_RESPONSE = "waiting for host response"
    WAITING_FOR_GUEST_RESPONSE = "waiting for guest response"
    WAITING_FOR_BOTH_RESPONSES = "waiting for host and guest response"
    GAME_FINISHED = "game finished"

    id = models.UUIDField(
        default=uuid.uuid4, primary_key=True, unique=True, editable=False
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    host = models.ForeignKey(
        "Player",
        on_delete=models.DO_NOTHING,
        related_name="as_host",
    )
    guest = models.ForeignKey(
        "Player",
        on_delete=models.DO_NOTHING,
        related_name="as_guest",
        blank=True,
        null=True,
    )
    answers = models.JSONField(default=list)
    name = models.CharField(max_length=200, blank=True, null=True)
    category = models.CharField(max_length=200, default="")

    @property
    def players(self):
        return self.host, self.guest

    @property
    def waiting_for_guest(self) -> bool:
        return self.status == self.WAITING_FOR_GUEST

    @property
    def game_is_finished(self) -> bool:
        return self.status == self.GAME_FINISHED

    @property
    def status(self) -> str:

        if not self.guest:
            return self.WAITING_FOR_GUEST

        guest_ans, host_ans = self.answers[-1]

        if all((host_ans, guest_ans, host_ans == guest_ans)):
            return self.GAME_FINISHED
        elif not host_ans and not guest_ans:
            return self.WAITING_FOR_BOTH_RESPONSES
        elif not host_ans:
            return self.WAITING_FOR_HOST_RESPONSE
        elif not guest_ans:
            return self.WAITING_FOR_GUEST_RESPONSE

    def answer_as_host(self, answer):
        guest_ans, host_ans = self.answers[-1]
        if host_ans:
            raise ValueError("Trying to modify old answer")
        self.answers[-1] = (guest_ans, answer)
        self.save()

    def answer_as_guest(self, answer):
        guest_ans, host_ans = self.answers[-1]
        if guest_ans:
            raise ValueError("Trying to modify old answer")
        self.answers[-1] = (answer, host_ans)
        self.save()

    @classmethod
    def start_game(cls, *, player: "Player", player_answer: str, category=""):
        answers = [(None, player_answer)]
        return cls.objects.create(host=player, answers=answers, category=category)

    def save(self, *args, **kwargs):
        if not self.pk and self.answers and self.answers[0]:
            raise ValueError("Wrong answers")

        last_guest_ans, last_host_ans = self.answers[-1]
        if last_host_ans and last_guest_ans:
            if last_host_ans != last_guest_ans:
                self.answers = self.answers + [(None, None)]
            else:
                self.answers = self.answers + [(last_guest_ans, last_host_ans)]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.created} {self.id} {self.status}"


class Player(models.Model):
    # do zmiany id gracza ? nie musi być uuid, tylko np. w oparciu o sesję?
    id = models.UUIDField(
        default=uuid.uuid4, primary_key=True, unique=True, editable=False
    )
    nickname = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)

    @property
    def games(self):
        query = Q(guest=self) | Q(host=self)
        return Game.objects.filter(query)

    def __str__(self):
        return f"{self.nickname}"
