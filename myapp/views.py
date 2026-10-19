from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Categories, Expense
from django.contrib import messages
from django.db.models import Sum

# Create your views here.


# user authintication
def user_login(request):
    if request.method == "POST":
        # Getting data ...........................
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        # if authinticate then user.username, user.password create hobe
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid username or passward")
    return render(
        request,
        "login.html",
    )


@login_required(login_url="login")
def user_logout(request):
    logout(request)
    return redirect("login")


def user_register(request):
    if request.method == "POST":
        # getting data form tha form
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # validationo
        if password1 != password2:
            messages.error(request, "Password did not matched")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username allready taken")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already taken")
        else:
            User.objects.create_user(username=username, email=email, password=password1)
            messages.success(
                request, "Account created successfully ! You can login now"
            )
            return redirect("login")

    return render(request, "register.html")


def password_reset_request(request):
    return render(request, "password_reset.html")


def password_reset_confirm(request):
    return render(request, "password_reset_confirm.html")


def password_reset_done(request):
    return render(request, "password_reset_done.html")


def password_reset_email(request):
    return render(request, "password_reset_email.html")


def password_reset_complete(request):
    return render(request, "password_reset_complete.html")


# base template
@login_required(login_url="login")
def home(request):
    result = (
        Expense.objects.filter(user=request.user)
        .values("category__name")
        .annotate(total=Sum("amount"))
    )
    grand_total = Expense.objects.filter(
        user=request.user
    ).aggregate(total=Sum("amount"))["total"] or 0
    context = {
        "result": result,
        "grand_total": grand_total,
    }
    return render(request, "home.html", context)


@login_required(login_url="login")
def expense_list(request):
    data = (
        Expense.objects.filter(user=request.user)
        .select_related("category")
        .order_by("-date")
    )
    context = {"data": data}
    return render(request, "expense_list.html", context)


@login_required(login_url="login")
def expense_create(request):
    category = Categories.objects.all()
    if request.method == "POST":
        category_id = request.POST.get("category")
        amount = request.POST.get("amount")
        description = request.POST.get("description")
        if not category_id:
            messages.error(request, "please select a category")
            return redirect("expense_create")
        Expense.objects.create(
            user=request.user,
            category_id=category_id,
            amount=amount,
            description=description,
        )
        messages.success(request, "Expense created successfully")
        return redirect("expense_list")
    context = {"category": category}
    return render(request, "expense_form.html", context)


@login_required(login_url="login")
def expense_update(request, expense_id):
    data = Expense.objects.get(user = request.user, id=expense_id)
    if request.method == "POST":
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description')

        if not category_id:
            messages.error(request, "Please select a category")
            return redirect("expense_update", expense_id=data.id)

        if not amount:
            messages.error(request, "Please add amount")
            return redirect("expense_update", expense_id=data.id)

        if not description:
            messages.error(request, "Please add description")
            return redirect("expense_update", expense_id=data.id)

        data.category_id=category_id
        data.amount= amount
        data.description = description
        data.save()

        messages.success(request, "Expense updated successfully!")
        return redirect("expense_list")
        
        
    category = Categories.objects.all()
    expense = Expense.objects.get(user=request.user, id=expense_id)
    context = {"category": category, "expense": expense}
    return render(request, "expense_form.html", context)


@login_required(login_url="login")
def expense_delete(request, expense_id):
    data = Expense.objects.get(user=request.user, id=expense_id)
    if request.method == "POST":
        data.delete()
        messages.success(request, "Expense delete successfully")
        return redirect("expense_list")
    context = {"data": data}
    return render(request, "expense_confirm_delete.html", context)
