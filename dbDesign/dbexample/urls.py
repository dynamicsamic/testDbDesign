from django.urls import path

from . import views

app_name = "dbexample"

urlpatterns = [path("", views.foo)]
