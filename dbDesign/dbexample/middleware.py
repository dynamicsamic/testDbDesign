from .models import Customer


def customer_middleware(get_response):
    def middleware(request):
        user = request.user

        if user.is_anonymous:
            customer = None
        else:
            customer, _ = Customer.objects.get_or_create(user=user)
        print(f"new middleware works: {request.user.is_anonymous=}")
        request.customer = customer
        response = get_response(request)

        return response

    return middleware
