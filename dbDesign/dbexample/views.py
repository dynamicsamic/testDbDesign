from django.contrib.auth.decorators import login_required
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render

from . import forms, models


@login_required
def foo(request: HttpRequest):
    user = request.user
    request.session["foo"] = "bar"
    print(request.session["foo"])
    print(dir(request.session))
    print(request.session.modified)
    request.session.flush()
    print(request.session.get("foo", "NONONO"))
    # print(dir(request.session))
    # print(request.session.session_key)
    return HttpResponse(request)


def customer_registration_view(request):
    form = forms.UserRegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password1"])
        user.save()  # somehow handle user.is_active
        customer = models.Customer.objects.create(user=user)
        models.Cart.objects.create(customer=customer)  # create an empty cart
        # return redirect

        return HttpResponse(request, status=201)
    return render(request, "some.html", {"form": form})
