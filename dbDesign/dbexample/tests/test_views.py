from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from .. import models


class ViewTestCase(TestCase):
    def setUp(self):
        self.unauthorized_client = Client()

    def test_customer_registration_with_valid_data_success(self):
        user_count = models.User.objects.count()
        customer_count = models.Customer.objects.count()
        valid_data = {
            "username": "sam",
            "email": "sam@hello.py",
            "password1": "hello",
            "password2": "hello",
        }
        response = self.unauthorized_client.post(
            path=reverse("dbexample:cusomer_registration"), data=valid_data
        )
        self.assertEqual(models.User.objects.count(), user_count + 1)
        self.assertEqual(models.Customer.objects.count(), customer_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
