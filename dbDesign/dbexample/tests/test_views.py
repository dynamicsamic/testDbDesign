from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .. import models

User = get_user_model()


class ViewTestCase(TestCase):
    def setUp(self):
        self.unauthorized_client = Client()

    def test_customer_registration_with_valid_data_success(self):
        user_count = User.objects.count()
        customer_count = models.Customer.objects.count()
        valid_data = {
            "username": "sam",
            "email": "sam@hello.py",
            "password1": "hello",
            "password2": "hello",
        }
        response = self.unauthorized_client.post(
            path=reverse("dbexample:customer_registration"), data=valid_data
        )
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertEqual(models.Customer.objects.count(), customer_count + 1)
        customer = models.Customer.objects.last()
        user = customer.user
        # self.assertEqual(customer.username, user.username)
        self.assertTupleEqual(
            (valid_data["username"], customer.username),
            (valid_data["username"], user.username),
        )
        self.assertTupleEqual(
            (valid_data["email"], customer.email),
            (valid_data["email"], user.email),
        )
        self.assertTrue(user.check_password(valid_data["password1"]))
