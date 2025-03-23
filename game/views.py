from django.http import JsonResponse
from django.shortcuts import redirect, render
from rest_framework import status

from .forms import GameForm, PlayerForm
from .models import Game, Player
from .utils import player_in_game


def index(request):
    """
    Strona główna aplikacji; powinny się wyświetlać na niej jakieś podstawowe
    informacje o grze, może instrukcja ?
    Różne widoki w zależności od tego, czy gracz jest zalogowany, czy nie;
    Wyrzucić patrzenie na sesje? - a może dodać opcje "zagraj jako gość" i wtedy
    nie trzeba by było się logować, żeby zagrać;
    :param request:
    :return:
    """
    player_id = request.session.get("player_id")
    context = {"player_id": player_id}
    return render(request, "game/index.html", context=context)


def new_game(request):
    """
    Widok rozpoczęcia nowej gry;
    :param request:
    :return:
    """
    # czy my chcemy zostawić forms tutaj?
    # czy ręcznie dać pole i wyciągnąć wartość javascriptem?
    # a następnie zweryfikować poprawność pola za pomocą serializatora
    form = GameForm()
    player_id = request.session.get("player_id")
    # Jeśli w sesji nie ma żadnego gracza (użytkownika lub niezalogowanego gościa)
    # to należy przekierować do widoku "nowego gracza"
    if not player_id:
        return redirect("new-player")

    # ten fragment pewnie do zmiany — wywalić stąd formularz i wrzucić dane
    # przesłane za pomocą javascriptu
    if request.method == "POST":
        form = GameForm(request.POST)
        # wersja bez formularza: sprawdzenie, czy dane są poprawne
        # za pomocą serializatora
        if form.is_valid():
            answer = form["word"].data
            # category = form["category"]
            player = Player.objects.get(id=player_id)
            game = Game.start_game(player=player, player_answer=answer)
            request.session["game_id"] = str(game.id)
            return redirect("game", str(game.id))

    context = {"form": form}
    return render(request, "game/new_game.html", context=context)


def game(request, pk: str):
    game = Game.objects.get(id=pk)
    player = Player.objects.get(id=request.session["player_id"])
    is_host = game.host == player
    context = {
        "game_id": game.id,
        "is_host": is_host,
        "host_nickname": game.host.nickname,
        "guest_nickname": "",
    }
    if game.guest:
        context["guest_nickname"] = game.guest.nickname
    return render(request, "game/game.html", context=context)


def join_game(request, pk: str):
    # To jest widok, który się wyświetla, jeśli zaproszony gracz wejdzie na
    # link z zaproszeniem

    # analogicznie jak do widoku nowej gry: nie chcemy raczej,
    # żeby tu był formularz, tylko żeby tu były ręcznie dodane pola
    form = GameForm()
    player_id = request.session.get("player_id")
    game = Game.objects.get(id=pk)
    # jeśli na link wszedł gracz, który wcześniej nie zalogował się/nie grał w grę
    # i nie jest zapisany w sesji, to przekierowywujemy go na stronę
    # z tworzeniem nowego gracza
    if not player_id:
        request.session["game_id"] = pk
        return redirect("new-player")

    # jeśli to host sobie wszedł na ten link, to chcemy go przekierować
    # na stronę gry
    if player_id == str(game.host.id):
        return redirect("game", str(game.id))

    # jeśli pobrany z sesji gracz nie jest hostem, to
    # jeśli gra już ma "obsadzonego" gościa:
    if not game.waiting_for_guest:
        if player_id == str(game.guest.id):
            return redirect("game", str(game.id))
        # zwracamy forbidden
        return JsonResponse(data={}, status=status.HTTP_403_FORBIDDEN)

    # w przeciwnym razie (czyli gra czeka cały czas na gościa):
    # tutaj kod do zmiany analogicznie jak w widoku `nowa gra`
    if request.method == "POST":
        answer = request.POST.get("word")
        if not answer:
            return JsonResponse(
                data={"error": "No `word` key"}, status=status.HTTP_400_BAD_REQUEST
            )
        player, created = Player.objects.get_or_create(id=player_id)
        game.guest = player
        game.answer_as_guest(answer)
        return redirect("game", str(game.id))
    context = {
        "form": form,
        "host_nickname": game.host.nickname,
        "game_id": str(game.id),
    }
    return render(request, "game/join_game.html", context=context)


def game_status(request, pk: str):
    game = Game.objects.get(id=pk)
    player_id = request.session.get("player_id")
    if not player_in_game(player_id, game):
        return JsonResponse(
            data={"error": "to jest test"}, status=status.HTTP_403_FORBIDDEN
        )

    is_host = player_id == str(game.host.id)
    is_guest = not is_host

    game_data = {
        "action": None,
        "answers": game.answers,
        "is_host": is_host,
        "host_nickname": game.host.nickname,
        "guest_nickname": None,
    }

    if game.waiting_for_guest:
        game_data["action"] = "wait_for_player"
        return JsonResponse(data=game_data)

    game_data["guest_nickname"] = game.guest.nickname

    if game.game_is_finished:
        game_data["action"] = "finished"
        return JsonResponse(data=game_data)
    if any(
        (
            game.status == Game.WAITING_FOR_BOTH_RESPONSES,
            is_host and game.status == Game.WAITING_FOR_HOST_RESPONSE,
            is_guest and game.status == Game.WAITING_FOR_GUEST_RESPONSE,
        )
    ):
        game_data["action"] = "get_response"
    else:
        game_data["action"] = "wait"

    return JsonResponse(data=game_data)


def answer(request, pk: str):
    # import ipdb; ipdb.set_trace()
    game = Game.objects.get(id=pk)
    player_id = request.session.get("player_id")

    if (
        not player_in_game(player_id, game)
        or game.waiting_for_guest
        or game.game_is_finished
    ):
        return JsonResponse(data={}, status=status.HTTP_403_FORBIDDEN)
    is_host = player_id == str(game.host.id)
    is_guest = not is_host
    answer = request.POST.get("word")

    if not answer:
        return JsonResponse(data={}, status=status.HTTP_400_BAD_REQUEST)

    if is_host and (game.WAITING_FOR_HOST_RESPONSE or game.WAITING_FOR_BOTH_RESPONSES):
        game.answer_as_host(answer)

    if is_guest and (
        game.WAITING_FOR_GUEST_RESPONSE or game.WAITING_FOR_BOTH_RESPONSES
    ):
        game.answer_as_guest(answer)

    game.refresh_from_db()
    if (
        game.status == Game.WAITING_FOR_BOTH_RESPONSES
        or (is_host and game.status == Game.WAITING_FOR_HOST_RESPONSE)
        or (is_guest and game.status == Game.WAITING_FOR_GUEST_RESPONSE)
    ):
        return_action = "get_response"
    else:
        return_action = "wait"
    game_data = {
        "action": return_action,
        "answers": game.answers,
        "is_host": is_host,
        "host_nickname": game.host.nickname,
        "guest_nickname": game.guest.nickname,
    }
    return JsonResponse(data=game_data)


def new_player(request):
    """
    Widok tworzenia nowego gracza (nie użytkownika!)
    :param request:
    :return:
    """
    player = request.session.get("player_id")
    if player:
        # tu zamiast robić redirecta na index powinniśmy cofnąć do strony,
        # z której wyszliśmy chyba
        # czyli chyba na url request.meta.HTTP_REFERER czy jakoś tak
        # chociaż w tym przypadku możnaby zostawić to przekierowanie na index?
        return redirect("index")
    # jeśli rzeczywiście nie mamy zalogowanego żadnego użytkownika
    # to chcemy wyświetlić dwie opcje:
    # graj jako gość
    # zaloguj/zarejestruj się --> ta opcja powinna przenosić do widoku logowania

    # jeśli ktoś wybrał opcję graj jako gość:
    # tworzymy formularz do utworzenia gracza
    # czy na pewno chcemy to robić za pomocą formularza?
    # czy może ręcznie stworzyć pola do uzupełnienia i następnie wysłać wartości
    # za pomocą javascriptu - bo i tak ręcznie tworzymy tego gracza koniec końców
    form = PlayerForm()
    context = {"form": form}
    # jeśli ktoś przesłał dane z formularza, czyli metoda == POST:
    if request.method == "POST":
        # pobieramy przesłane dane
        form = PlayerForm(request.POST)
        if form.is_valid():
            # tworzymy gracza o danych wartościach
            player = Player.objects.create(nickname=form["nickname"].data)
            # ustawiamy w sesji id gracza
            request.session["player_id"] = str(player.id)
            if "game_id" in request.session:
                game_id = request.session.pop("game_id")
                return redirect("invite", game_id)
            return redirect("new-game")
    return render(request, "game/new_player.html", context=context)


def my_games(request):
    player_id = request.session.get("player_id")
    player = Player.objects.get(id=player_id)
    if not player:
        return redirect("index")
    games = player.games.order_by("-updated")
    context = {"games": games}
    return render(request, "game/my_games.html", context=context)
