
from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [

    path('home/', views.homePage, name='home'),

    path('mytmc/', views.mytmc, name='mytmc'),
    path('history/', views.history, name='history'),
    path('excange/', views.excange, name='excange'),
    # path('profile/', views.profile, name='profile'),

]
