
from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('',views.redir,name = 'redirect'),

    path('home/', views.homePage, name='home'),
    path('mytmc/', views.mytmc, name='mytmc'),
    path('history/', views.history, name='history'),
    path('exchange/', views.exchange, name='exchange'),
    path('profile/', views.profile, name='profile'),
    path('login/', views.login, name='login'),
    path('registration/', views.reg, name='register'),

]
