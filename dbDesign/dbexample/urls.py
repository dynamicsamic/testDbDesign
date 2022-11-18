from django.urls import path

from . import views

app_name = "dbexample"

urlpatterns = [
    path("", views.foo, name="foo"),
    path(
        "signup/",
        views.customer_registration_view,
        name="customer_registration",
    ),
]
