from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render

from . import forms, models


def foo(request: HttpRequest):
    user = request.user
    return HttpResponse(request.customer)


def customer_registration_view(request):
    if request.method == "POST":
        form = forms.UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            models.Customer.objects.create(user=user)

    return HttpResponse(request, status=201)
