from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
# Create your views here.

#user authintication
def user_login(request):

    return render(request,'login.html',)

def user_logout(request):
    return redirect('login')


def user_register(request):
    if request.method == "POST":
        #getting data form tha form
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        #validationo
        if  password1 !=  password2:
            messages.error(request,"Password did not matched")
        elif User.objects.filter(username=username).exists():
            messages.error(request,"Username allready taken")
        elif User.objects.filter(email=email).exists():
            messages.error(request,"Email already taken")
        else:
            User.objects.create_user(
                username = username,
                email = email,
                password = password1
            )
            messages.success(request,"Account created successfully ! You can login now")
            return redirect('login')

    return render(request,'register.html')


def password_reset_request(request):
    return render(request,'password_reset.html')

def password_reset_confirm(request):
    return render(request,'password_reset_confirm.html')

def password_reset_done(request):
    return render(request,'password_reset_done.html')

def password_reset_email(request):
    return render(request,'password_reset_email.html')

def password_reset_complete(request):
    return render(request,'password_reset_complete.html')

# base template
def home(request):
    return render(request,'home.html')

def expense_list(request):
    return render(request,'expense_list.html')


def expense_create(request):
    return render(request,'expense_form.html')

def expense_update(request):
    return render(request,'expense_form.html')

def expense_delete(request):
    return render(request,'expense_confirm_delete.html')