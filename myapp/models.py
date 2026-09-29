from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Categories(models.Model):
    name = models.CharField(100,null=False,blank=False)

class Expense(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    category = models.ForeignKey(Categories,on_delete=models.SET_NULL,null=True)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)