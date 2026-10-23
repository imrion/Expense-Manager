from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Categories, Expense
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib import messages
from django.db.models import Sum
from django.db.models import Q, Count
from django.conf import settings
from django.utils import timezone
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal

# Create your views here.


def _clean_expense_amount(value):
    try:
        return forms.DecimalField(
            max_digits=10,
            decimal_places=2,
            min_value=Decimal("0.01"),
        ).clean(value)
    except ValidationError:
        return None


# user authintication
def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")
    password_reset_success = (
        request.GET.get("password_reset") == "success"
    )

    context = {
        "password_reset_success": password_reset_success
    }

    if request.method == "POST":
        # Getting data
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(
                request,
                "Invalid username or password"
            )

    return render(request, "login.html", context)


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
    if request.method == "POST":
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            domain = get_current_site(request).domain
            reset_link = f"http://{domain}/password_reset_confirm/{uid}/{token}"
            # send mail
            subject = "password_reset_confirm"
            message = render_to_string("password_reset_email.html",{"reset_link":reset_link})
            sent = send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            print("Email sent:", sent)
            messages.success(request, "A password reset link has been set to your email")
            return redirect('password_reset_done')
        else:
            messages.error(request, "User not found")

    return render(request, "password_reset.html")


def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except(user.DoesNotExist,ValueError,TypeError):
        messages.error(request,"Invalid reset link")
        return redirect('password_reset_request')

    if not default_token_generator.check_token(user,token):
        messages.error(request,"Invalid or expired reset link")
        return redirect('password_reset_request')

    if request.method == "POST":
        new_password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')

        if new_password != confirm_password:
            messages.error(request,"Password not match")
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request,"Passowrd reset successfully")
            return redirect('password_reset_complete')
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
    today = timezone.localdate()
    all_expenses = Expense.objects.filter(user=request.user)
    expenses = all_expenses
    categories = Categories.objects.filter(Q(user__isnull=True) | Q(user=request.user))
    search = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    month = request.GET.get("month")
    if month is None:
        month = today.strftime("%Y-%m")
    if search:
        expenses = expenses.filter(Q(description__icontains=search) | Q(category__name__icontains=search))
    if category_id.isdigit() and categories.filter(id=int(category_id)).exists():
        expenses = expenses.filter(category_id=int(category_id))
    else:
        category_id = ""
    if not month:
        month_label = "All time"
    elif len(month) == 7 and month[4] == "-" and month[:4].isdigit() and month[5:].isdigit():
        year, month_number = map(int, month.split("-"))
        if 1 <= year <= 9999 and 1 <= month_number <= 12:
            expenses = expenses.filter(date__year=year, date__month=month_number)
            month_label = timezone.datetime(year, month_number, 1).strftime("%B %Y")
        else:
            month = ""
            month_label = "All time"
    else:
        month = ""
        month_label = "All time"
    month_expenses = expenses
    result = (
        expenses
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    grand_total = all_expenses.aggregate(total=Sum("amount"))["total"] or 0
    month_total = month_expenses.aggregate(total=Sum("amount"))["total"] or 0
    month_count = month_expenses.count()
    recent_expenses = expenses.select_related("category").order_by("-date", "-id")[:5]
    context = {
        "result": result,
        "grand_total": grand_total,
        "month_total": month_total,
        "month_count": month_count,
        "recent_expenses": recent_expenses,
        "category_count": result.count(),
        "month_label": month_label,
        "categories": categories,
        "search": search,
        "selected_category": category_id,
        "selected_month": month,
        "has_filters": bool(search or category_id or not month or month != today.strftime("%Y-%m")),
    }
    return render(request, "home.html", context)


@login_required(login_url="login")
def expense_list(request):
    data = Expense.objects.filter(user=request.user)
    search = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    month = request.GET.get("month", "")
    if search:
        data = data.filter(Q(description__icontains=search) | Q(category__name__icontains=search))
    if category_id.isdigit():
        data = data.filter(category_id=int(category_id))
    if len(month) == 7 and month[4] == "-" and month[:4].isdigit() and month[5:].isdigit():
        year, month_number = map(int, month.split("-"))
        if 1 <= year <= 9999 and 1 <= month_number <= 12:
            data = data.filter(date__year=year, date__month=month_number)
    data = (
        data
        .select_related("category")
        .order_by("-date", "-id")
    )
    context = {
        "data": data,
        "categories": Categories.objects.filter(Q(user__isnull=True) | Q(user=request.user)).order_by("name"),
        "search": search,
        "selected_category": category_id,
        "selected_month": month,
        "filtered_total": data.aggregate(total=Sum("amount"))["total"] or 0,
        "filtered_count": data.count(),
        "has_filters": bool(search or category_id or month),
    }
    return render(request, "expense_list.html", context)


@login_required(login_url="login")
def expense_create(request):
    category = Categories.objects.filter(Q(user__isnull=True) | Q(user=request.user))
    if request.method == "POST":
        category_id = request.POST.get("category")
        amount = _clean_expense_amount(request.POST.get("amount"))
        description = request.POST.get("description", "").strip()
        if not category_id:
            messages.error(request, "Please select a category")
            return redirect("expense_create")
        if amount is None:
            messages.error(request, "Enter an amount greater than zero with up to two decimal places.")
            return redirect("expense_create")
        if not description:
            messages.error(request, "Please add a description")
            return redirect("expense_create")
        if not category.filter(id=category_id).exists():
            messages.error(request, "Please choose one of your available categories")
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
    data = get_object_or_404(Expense, user=request.user, id=expense_id)
    if request.method == "POST":
        category_id = request.POST.get('category')
        amount = _clean_expense_amount(request.POST.get('amount'))
        description = request.POST.get('description', '').strip()

        if not category_id:
            messages.error(request, "Please select a category")
            return redirect("expense_update", expense_id=data.id)

        if amount is None:
            messages.error(request, "Enter an amount greater than zero with up to two decimal places.")
            return redirect("expense_update", expense_id=data.id)

        if not description:
            messages.error(request, "Please add description")
            return redirect("expense_update", expense_id=data.id)

        available_categories = Categories.objects.filter(Q(user__isnull=True) | Q(user=request.user))
        if not available_categories.filter(id=category_id).exists():
            messages.error(request, "Please choose one of your available categories")
            return redirect("expense_update", expense_id=data.id)
        data.category_id=category_id
        data.amount= amount
        data.description = description
        data.save()

        messages.success(request, "Expense updated successfully!")
        return redirect("expense_list")
        
        
    category = Categories.objects.filter(Q(user__isnull=True) | Q(user=request.user))
    expense = data
    context = {"category": category, "expense": expense}
    return render(request, "expense_form.html", context)


@login_required(login_url="login")
def expense_delete(request, expense_id):
    data = get_object_or_404(Expense, user=request.user, id=expense_id)
    if request.method == "POST":
        data.delete()
        messages.success(request, "Expense delete successfully")
        return redirect("expense_list")
    context = {"data": data}
    return render(request, "expense_confirm_delete.html", context)


@login_required(login_url="login")
def profile(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        if not username or not email:
            messages.error(request, "Username and email are required.")
        elif User.objects.filter(username__iexact=username).exclude(pk=request.user.pk).exists():
            messages.error(request, "That username is already in use.")
        elif User.objects.filter(email__iexact=email).exclude(pk=request.user.pk).exists():
            messages.error(request, "That email is already in use.")
        else:
            request.user.username = username
            request.user.email = email
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("profile")
    return render(request, "profile.html")


@login_required(login_url="login")
def category_list(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "Enter a category name.")
        elif len(name) > 100:
            messages.error(request, "Category names must be 100 characters or fewer.")
        elif Categories.objects.filter(user=request.user, name__iexact=name).exists():
            messages.error(request, "You already have a category with that name.")
        else:
            Categories.objects.create(user=request.user, name=name)
            messages.success(request, f"{name} category created.")
            return redirect("category_list")
    context = {
        "categories": Categories.objects.filter(Q(user__isnull=True) | Q(user=request.user)),
        "custom_categories": Categories.objects.filter(user=request.user),
    }
    return render(request, "category_list.html", context)


@login_required(login_url="login")
def category_delete(request, category_id):
    category = get_object_or_404(Categories, id=category_id, user=request.user)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted. Existing expenses were kept without a category.")
    return redirect("category_list")
