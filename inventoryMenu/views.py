from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from .models import User
import os, hashlib, secrets

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

def reg(request):
    if request.method == 'POST':
        email_get = request.POST["email"]
        fullname_get = request.POST["fullname"].split()
        lastname = fullname_get[0].capitalize() if len(fullname_get) > 0 else ""
        firstname = fullname_get[1].capitalize() if len(fullname_get) > 1 else ""
        middlename = fullname_get[2].capitalize() if len(fullname_get) > 2 else ""
        number_get = request.POST["number"]
        password_get = request.POST["password"].encode()

        salt = os.urandom(16)
        hash_password = hashlib.pbkdf2_hmac('sha256', password_get, salt, 100000)


        user = User.objects.create(email = email_get,
                                   first_name = firstname,
                                   last_name = lastname,
                                   middle_name = middlename,
                                   phone = number_get,
                                   password = hash_password.hex(),
                                   salt_password=salt.hex())

        request.session['user_id'] = user.id
        request.session['user_email'] = user.email
        request.session['role'] = user.role

        return redirect('home')


    return render(request, "register.html")


def login(request):
    if request.method == 'POST':
        email_get = request.POST["email"]
        password_get = request.POST["password"].encode()


        print( email_get, password_get)
    return render(request, "login.html")
