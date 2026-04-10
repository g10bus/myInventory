from django.shortcuts import render, redirect

# Create your views here.


def redir(request):
  return redirect('home',permanent=True)


def homePage(request):
    return render(request, "main.html")

def mytmc(request):
    return render(request, "tmc.html")


def history(request):
    return render(request, "history.html")


def exchange(request):
    return render(request, "exchange.html")


def profile(request):
    return render(request, "profile.html")

def registr(request):
    return render(request, "registr.html")

def login(request):
    return render(request, "login.html")