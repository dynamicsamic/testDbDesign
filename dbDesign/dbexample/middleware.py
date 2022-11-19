from .models import Customer


def customer_middleware(get_response):
    def middleware(request):
        customer = None
        user = request.user

        # if user.is_anonymous:
        #    customer = None
        # else:
        #    customer, _ = Customer.objects.get_or_create(user=user)
        if qs := Customer.objects.filter(user_id=user.id):
            customer = qs[0]
        request.customer = customer
        response = get_response(request)

        return response

    return middleware
