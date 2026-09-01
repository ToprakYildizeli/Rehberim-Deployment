from django.contrib.auth import login
from django.shortcuts import render, redirect

from .forms import CounselorRegisterForm


def register_request(request):
    """Rehber kaydı. Başarılı olursa oturum açtırıp dashboard'a yönlendirir."""
    if request.method == "POST":
        form = CounselorRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = CounselorRegisterForm()
    return render(request, "accounts/register.html", {"form": form})
