from django.urls import path

from . import views

app_name = "dbexample"

urlpatterns = [
    path(
        "signup/",
        views.customer_registration_view,
        name="cusomer_registration",
    )
]
