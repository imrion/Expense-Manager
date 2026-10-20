from django.test import TestCase
from django.urls import reverse


class LoginHeadingTests(TestCase):
    def test_normal_login_shows_welcome(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["password_reset_success"])
        self.assertContains(response, "<h3 class=\"fw-bold text-dark\">Welcome</h3>", html=True)
        self.assertNotContains(response, "Welcome Back")

    def test_password_reset_login_link_shows_welcome_back(self):
        response = self.client.get(
            reverse("login"),
            {"password_reset": "success"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["password_reset_success"])
        self.assertContains(response, "Welcome Back")

    def test_password_reset_completion_links_to_welcome_back_login(self):
        response = self.client.get(reverse("password_reset_complete"))

        self.assertContains(
            response,
            f'href="{reverse("login")}?password_reset=success"',
        )
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
