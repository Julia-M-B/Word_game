from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from rest_framework import status


def login_page(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not (username and password):
            return JsonResponse(
                data={"error": "missing username and/or password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse(
                data={"action": "register"}, status=status.HTTP_404_NOT_FOUND
            )

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            request.session["player_id"] = str(user.player.id)
            return JsonResponse(
                {"action": "redirect", "redirect_url": reverse("index")}
            )
        else:
            return JsonResponse(
                data={"error": "wrong password, authentication failed"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    return render(request, "user/login_register.html")


@login_required
def logout_page(request):
    logout(request)
    return redirect("index")
