from django.shortcuts import render, redirect
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
from django.conf import settings

# Create your views here.


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
