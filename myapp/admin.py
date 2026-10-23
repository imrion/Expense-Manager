from django.contrib import admin
from .models import Categories, Expense
# Register your models here.


@admin.register(Categories)
class categoryadmin(admin.ModelAdmin):
    list_display =['id','name','user']
    search_fields = ['name','user__username']
    ordering = ['name']

@admin.register(Expense)
class Expenseadmin(admin.ModelAdmin):
    list_display =['id','amount','category__name','user__username','description','date']
    search_fields = ['id']
    ordering = ['-date']
