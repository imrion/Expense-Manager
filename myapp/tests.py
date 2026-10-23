from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Categories, Expense


class LoginHeadingTests(TestCase):
    def test_normal_login_shows_welcome(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["password_reset_success"])
        self.assertContains(response, "<h3 class=\"fw-bold text-dark\">Welcome</h3>", html=True)
        self.assertNotContains(response, "Welcome Back")
    def test_password_reset_login_link_shows_welcome_back(self):
        response = self.client.get(reverse("login"), {"password_reset": "success"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["password_reset_success"])
        self.assertContains(response, "Welcome Back")

    def test_password_reset_completion_links_to_welcome_back_login(self):
        response = self.client.get(reverse("password_reset_complete"))
        self.assertContains(response, f'href="{reverse("login")}?password_reset=success"')
        self.assertContains(response, "Back to Login")

    def test_invalid_credentials_keep_error_message_and_normal_heading(self):
        response = self.client.post(
            reverse("login"),
            {"username": "unknown-user", "password": "invalid-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["password_reset_success"])
        self.assertContains(response, "Invalid username or password")
        self.assertContains(response, "Welcome")
        self.assertNotContains(response, "Welcome Back")


class ExpenseManagerFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="test-pass-123")
        self.other_user = User.objects.create_user(username="bob", password="test-pass-123")
        self.food = Categories.objects.create(name="Food")
        self.travel = Categories.objects.create(name="Travel")
        self.custom = Categories.objects.create(name="Books", user=self.user)
        self.client.force_login(self.user)

    def add_expense(self, *, category, amount, description, date=None):
        expense = Expense.objects.create(
            user=self.user,
            category=category,
            amount=amount,
            description=description,
        )
        if date:
            Expense.objects.filter(pk=expense.pk).update(date=date)
            expense.refresh_from_db()
        return expense

    def test_authenticated_pages_render(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("expense_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("expense_create")).status_code, 200)
        self.assertEqual(self.client.get(reverse("profile")).status_code, 200)
        self.assertEqual(self.client.get(reverse("category_list")).status_code, 200)

    def test_profile_updates_and_rejects_duplicate_username(self):
        response = self.client.post(reverse("profile"), {
            "username": "alice-new", "email": "alice@example.com",
            "first_name": "Alice", "last_name": "Smith",
        })
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "alice-new")
        self.assertEqual(self.user.first_name, "Alice")

        response = self.client.post(reverse("profile"), {
            "username": "bob", "email": "alice2@example.com",
            "first_name": "Changed", "last_name": "Name",
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "alice-new")

    def test_custom_categories_are_private_and_can_be_deleted(self):
        response = self.client.post(reverse("category_list"), {"name": "  Garden  "})
        self.assertRedirects(response, reverse("category_list"))
        garden = Categories.objects.get(user=self.user, name="Garden")
        self.assertContains(self.client.get(reverse("category_list")), "Garden")

        self.client.force_login(self.other_user)
        response = self.client.get(reverse("category_list"))
        self.assertNotContains(response, "Garden")
        self.assertEqual(self.client.post(reverse("category_delete", args=[garden.pk])).status_code, 404)

        self.client.force_login(self.user)
        expense = self.add_expense(category=garden, amount="8.00", description="Plant seeds")
        response = self.client.post(reverse("category_delete", args=[garden.pk]))
        self.assertRedirects(response, reverse("category_list"))
        expense.refresh_from_db()
        self.assertIsNone(expense.category)

    def test_expense_create_update_and_cross_user_category_guard(self):
        response = self.client.post(reverse("expense_create"), {
            "category": self.custom.pk, "amount": "14.25", "description": "New book",
        })
        self.assertRedirects(response, reverse("expense_list"))
        expense = Expense.objects.get(description="New book")
        self.assertEqual(expense.user, self.user)

        private_category = Categories.objects.create(name="Secret", user=self.other_user)
        response = self.client.post(reverse("expense_create"), {
            "category": private_category.pk, "amount": "5.00", "description": "Invalid",
        })
        self.assertRedirects(response, reverse("expense_create"))
        self.assertFalse(Expense.objects.filter(description="Invalid").exists())

        response = self.client.post(reverse("expense_update", args=[expense.pk]), {
            "category": self.food.pk, "amount": "18.00", "description": "Updated book",
        })
        self.assertRedirects(response, reverse("expense_list"))
        expense.refresh_from_db()
        self.assertEqual(expense.description, "Updated book")
        self.assertEqual(expense.amount, 18)

    def test_invalid_expense_amounts_are_rejected_without_server_error(self):
        for value in ("abc", "0", "-4.50", "1.239", "100000000.00"):
            response = self.client.post(reverse("expense_create"), {
                "category": self.food.pk, "amount": value, "description": "Invalid amount",
            })
            self.assertRedirects(response, reverse("expense_create"))
        self.assertFalse(Expense.objects.filter(description="Invalid amount").exists())

        expense = self.add_expense(category=self.food, amount="2.00", description="Valid amount")
        response = self.client.post(reverse("expense_update", args=[expense.pk]), {
            "category": self.food.pk, "amount": "abc", "description": "Valid amount",
        })
        self.assertRedirects(response, reverse("expense_update", args=[expense.pk]))
        expense.refresh_from_db()
        self.assertEqual(expense.amount, 2)

    def test_empty_dashboard_filter_month_shows_all_matching_history(self):
        today = timezone.localdate()
        prior_year = today.replace(year=today.year - 1) if today.year > 1 else today
        self.add_expense(category=self.food, amount="7.00", description="Yesterday", date=prior_year)
        response = self.client.get(reverse("home"), {"month": "", "category": self.food.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["month_count"], 1)
        self.assertEqual(response.context["month_total"], 7)

    def test_expense_update_and_delete_do_not_expose_other_users_records(self):
        other_expense = Expense.objects.create(
            user=self.other_user, category=self.food, amount="3.00", description="Private",
        )
        self.assertEqual(self.client.get(reverse("expense_update", args=[other_expense.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("expense_delete", args=[other_expense.pk])).status_code, 404)

    def test_home_and_transaction_filters_match_category_month_and_search(self):
        today = timezone.localdate()
        this_month = today.replace(day=1)
        current = self.add_expense(category=self.food, amount="12.00", description="Lunch", date=today)
        self.add_expense(category=self.custom, amount="45.00", description="Book shop", date=today)
        old_date = this_month.replace(year=this_month.year - 1) if this_month.year > 1 else this_month
        self.add_expense(category=self.food, amount="99.00", description="Old lunch", date=old_date)

        filters = {"q": "lunch", "category": self.food.pk, "month": today.strftime("%Y-%m")}
        home = self.client.get(reverse("home"), filters)
        self.assertEqual(home.status_code, 200)
        self.assertEqual(home.context["month_count"], 1)
        self.assertEqual(home.context["month_total"], 12)
        self.assertEqual(list(home.context["recent_expenses"]), [current])

        listing = self.client.get(reverse("expense_list"), filters)
        self.assertEqual(list(listing.context["data"]), [current])
        self.assertEqual(listing.context["filtered_total"], 12)

    def test_expense_string_representation_is_text(self):
        expense = self.add_expense(category=self.food, amount="2.50", description="Coffee")
        self.assertIn("Coffee", str(expense))
