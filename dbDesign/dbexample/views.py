from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render


def foo(request: HttpRequest):
    user = request.user
    return HttpResponse(request.customer)
