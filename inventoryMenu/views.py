from django.shortcuts import render

# Create your views here.

def homePage(request):
    return render(request, "main.html")

def mytmc(request):
    return render(request, "tmc.html")


def history(request):
    return render(request, "history.html")


def excange(request):
    return render(request, "exchange.html")

#
# def profile(request):
#     return render(request, "profile.html")

