from django.utils import timezone
from django.db import models



# Create your models here.
class User(models.Model):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150,blank=True)
    last_name = models.CharField(max_length=150,blank=True)
    middle_name = models.CharField(max_length=150,blank=True)
    is_active = models.BooleanField(default=True)
    phone = models.CharField(max_length=20,blank=True)
    role = models.CharField(max_length=20,blank=True,default = "Сотрудник")
    password = models.CharField()
    salt_password = models.CharField()