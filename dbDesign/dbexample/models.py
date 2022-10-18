import datetime as dt

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from .exceptions import EmptyQuerySet, NotEnoughProductLeft, TooBigToAdd

MAX_AMOUNT_ADDED = 10000


class SelectRelatedManager(models.Manager):
    def __init__(self, select_related_model_name: str) -> None:
        super().__init__()
        self.select_related_model_name = select_related_model_name

    def get_queryset(self) -> QuerySet:
        """Join related object's data to main queryset."""
        queryset = super().get_queryset()
        return queryset.select_related(self.select_related_model_name)


class CustomerManager(SelectRelatedManager):
    def create(self, **kwargs):
        """Create an empty cart when creating a customer."""
        customer = super().create(**kwargs)
        Cart.objects.create(customer=customer)
        return customer


class BaseUser(AbstractUser):
    email = models.EmailField(_("email adress"), unique=True)

    class Meta:
        abstract = True


class User(BaseUser):
    is_active = models.BooleanField(
        _("active"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )


class Customer(models.Model):
    class CustomerStatus(models.TextChoices):
        CREATED = "created"
        ACTIVE = "active"
        FROZEN = "frozen"
        ARCHIVED = "archived"

    objects = CustomerManager("user")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="customer",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        _("Customer status"),
        max_length=20,
        choices=CustomerStatus.choices,
        default=CustomerStatus.CREATED,
        help_text=_("required, default: created"),
    )
    phone_number = models.CharField(
        _("Customer phone number"),
        max_length=15,
        help_text=_("required, max_len: 15"),
    )

    @property
    def username(self) -> str:
        return self.user.get_username()

    @property
    def email(self) -> str:
        return self.user.email

    @email.setter
    def email(self, new_email: str) -> None:
        self.user.email = new_email

    @property
    def first_name(self) -> str:
        return self.user.first_name

    @first_name.setter
    def first_name(self, new_first_name: str) -> None:
        self.user.first_name = new_first_name

    @property
    def last_name(self) -> str:
        return self.user.last_name

    @last_name.setter
    def last_name(self, new_last_name: str) -> None:
        self.user.last_name = new_last_name

    @property
    def full_name(self) -> str:
        return self.user.get_full_name()

    @property
    def last_login(self) -> dt.datetime or None:
        return self.user.last_login

    @property
    def date_joined(self) -> dt.datetime:
        return self.user.date_joined

    @property
    def is_active(self) -> bool:
        return self.user.is_active

    @property
    def is_anonymous(self) -> bool:
        return self.user.is_anonymous

    @property
    def is_authenticated(self) -> bool:
        return self.user.is_authenticated

    @property
    def groups(self):
        return self.user.groups

    def __str__(self) -> str:
        return self.username


class Employee(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="employee",
        on_delete=models.CASCADE,
    )


'''
class Address(models.Model):
    """Physical address."""

    class Elevator(models.TextChoices):
        """Elevator type."""

        REGULAR = "regular"
        CARGO = "cargo"
        COMBINED = "combined"
        NONE = "none"

    country = models.CharField(
        _("name of the country"),
        max_length=120,
        help_text="required, max_len: 120",
    )
    subregion = ...
    town = ...
    street = ...
    building = ...
    floor = ...
    elevator = models.CharField(
        _("elevator type"),
        max_length=10,
        choices=Elevator.choices,
        blank=True,
        null=True,
        help_text=_("optional"),
    )
    zip_code = ...
'''


class Agent(models.Model):
    name = models.CharField(
        _("name of the agent/partner"),
        max_length=150,
        unique=True,
        help_text=_("required, max_len: 150"),
    )
    # adress = models.ForeignKey(
    #    Address, related_name="agents", on_delete=models.PROTECT
    # )
    address = models.CharField(max_length=200)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Supplier(Agent):
    pass


class Vendor(models.Model):
    name = models.CharField(
        _("manufacturer name"),
        max_length=150,
        unique=True,
        help_text=_("required, max_len: 150"),
    )
    description = models.TextField(
        _("product vendor brief info"),
        max_length=2000,
        blank=True,
        null=True,
        help_text=_("optional, max_len: 2000"),
    )


class Brand(models.Model):
    name = models.CharField(
        _("brand name"),
        max_length=150,
        unique=True,
        help_text=_("required, max_len: 150"),
    )
    description = models.TextField(
        _("brand brief info"),
        max_length=2000,
        blank=True,
        null=True,
        help_text=_("optional, max_len: 2000"),
    )
    logo = models.CharField(_("replace this to imagefield"), max_length=30)
    vendor = models.ForeignKey(
        Vendor,
        related_name="brands",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(
        _("type of product"),
        max_length=150,
        unique=True,
        help_text=_("required, max_len: 150"),
    )
    logo = models.CharField(_("replace this to imagefield"), max_length=30)

    # maybe add an `attribute_collection (attr_set)` M2M field to have all
    # product attributes predefined before creation of a product_item

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    """
    Category for products.
    """

    name = models.CharField(
        _("product category name"),
        max_length=100,
        unique=True,
        help_text=_("required, max_len: 100"),
    )
    slug = models.SlugField(
        _("product category url"),
        max_length=150,
        unique=True,
        help_text=_(
            "required, allowed=[letters, numbers, hyphens, underscore], max_len: 150"
        ),
    )
    is_active = models.BooleanField(
        _("product category active status"),
        default=True,
        help_text=_("optional, defalut: True"),
    )

    class Meta:
        verbose_name = _("Product category")
        verbose_name_plural = _("Product categories")

    def __str__(self):
        return self.name


class ProductSet(models.Model):
    """
    A set of products (like particular model of a laptop).
    """

    web_id = models.CharField(
        _("product_set web id"),
        unique=True,
        max_length=50,
        help_text=_("required, numbers"),
    )
    slug = models.SlugField(
        _("product_set url"),
        max_length=255,
        help_text=_(
            "required, allowed=[letters, numbers, hyphens, underscore], max_len: 255"
        ),
    )
    name = models.CharField(
        _("product_set name"),
        max_length=150,
        help_text=_("required, max_len: 150"),
    )
    description = models.TextField(
        _("product_set description"),
        max_length=2000,
        help_text=_("required, max_len: 2000"),
    )
    categories = models.ManyToManyField(
        ProductCategory,
        related_name="productsets",
        # verbose_name=_("productset categories"),
    )
    p_type = models.ForeignKey(
        ProductType, related_name="productsets", on_delete=models.PROTECT
    )
    brand = models.ForeignKey(
        Brand, related_name="productsets", on_delete=models.PROTECT
    )
    is_active = models.BooleanField(
        _("product_set status"),
        default=False,
        help_text=_("bool; optional; default: False"),
    )
    created_at = models.DateTimeField(
        _("product_set creation time"),
        auto_now_add=True,
        help_text=_("format: Y-m-d H:M:S"),
    )
    updated_at = models.DateTimeField(
        _("product_set last update time"),
        auto_now=True,
        help_text=_("format: Y-m-d H:M:S"),
    )

    def __str__(self):
        return self.name


class ProductAttribute(models.Model):
    """Attribute of a product.
    Like `cpu`, `storage`, `RAM` etc.
    """

    name = models.CharField(
        _("product item attribute name"),
        max_length=150,
        unique=True,
        help_text=_("required, max_len: 150"),
    )

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    """Value of a product attribute."""

    class MyMan(models.Manager):
        def get_queryset(self) -> QuerySet:
            """Join related object's data to main queryset."""
            queryset = super().get_queryset()
            return queryset.select_related("attr")

    # objects = SelectRelatedManager(select_related_model_name="attr")
    attr = models.ForeignKey(
        ProductAttribute, related_name="values", on_delete=models.PROTECT
    )
    value = models.CharField(
        _("attribute value"),
        max_length=255,
        unique=True,
        help_text=_("required, max_length: 255"),
    )
    objects = MyMan()  # related_descriptor conflict

    def __str__(self):
        return f"{self.attr}: {self.value}"


class ProductItem(models.Model):
    """Particular item of product with specific attributes."""

    sku = models.CharField(
        _("stock keeping unit"),
        max_length=20,
        help_text="required, max_len: 20",
    )
    product_set = models.ForeignKey(
        ProductSet, related_name="items", on_delete=models.CASCADE
    )
    attrs = models.ManyToManyField(
        ProductAttributeValue,
        related_name="product_items",
        through="ProductToAttributeLinkTable",
    )
    # images = models.ForeignKey(
    #    ImageSet, related_name="product_items", on_delete=models.SET_DEFAULT
    # )
    regular_price = models.DecimalField(
        _("product item regular price"),
        max_digits=9,
        decimal_places=2,
        help_text=_("required, max_price: 9_999_999.99"),
    )
    discount_price = models.DecimalField(
        _("product item discount price"),
        max_digits=9,
        decimal_places=2,
        help_text=_("required, max_price: 9_999_999.99"),
    )
    # discount = models.ManyToManyField(Discount)
    is_active = models.BooleanField(
        _("product item status"),
        default=False,
        help_text=_("bool; optional; default: False"),
    )
    _view_count = models.PositiveIntegerField(
        _("number of views"), default=0, help_text="required, starts with 0"
    )
    made_in = models.CharField(_("change this to country FK"), max_length=150)
    created_at = models.DateTimeField(
        _("product item creation time"),
        auto_now_add=True,
        help_text=_("format: Y-m-d H:M:S"),
    )
    updated_at = models.DateTimeField(
        _("product item last update time"),
        auto_now=True,
        help_text=_("format: Y-m-d H:M:S"),
    )

    def __str__(self):
        # this queries the product_set. Need to change to select_related or
        # to remove link to product_set
        return f"{self.product_set.name}: {self.sku}"

    @property
    def views(self):
        return self._view_count

    def increment_view_count(self):
        self._view_count += 1
        self.save()


class ProductToAttributeLinkTable(models.Model):
    """Link table for product items and attribute values."""

    # Maybe it's more convinient to include attrs and their values to
    # ProductItems JSONField. Need to think about it.

    product_item = models.ForeignKey(ProductItem, on_delete=models.PROTECT)
    attr_values = models.ForeignKey(
        ProductAttributeValue,
        related_name="prod_items",
        on_delete=models.PROTECT,
    )

    # objects = SelectRelatedManager("product_item")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product_item", "attr_values"],
                name="unique_product_attr",
            )
        ]


"""
class Media(models.Model):
    product_item = models.ForeignKey(
        ProductItem, related_name="media", on_delete=models.CASCADE
    )
    image = models.ImageField(
        _("product item image"),
        upload_to="/images",
        default="/images/default.jpg",
        help_text="required, default: default.jpg",
    )
    is_cover = models.BooleanField(
        _("is a cover image"),
        default=False,
        help_text="reuqired, default: False",
    )
    created_at = models.DateTimeField(
        _("image creation time"),
        auto_now_add=True,
        help_text=_("format: Y-m-d H:M:S"),
    )
    updated_at = models.DateTimeField(
        _("image last update time"),
        auto_now=True,
        help_text=_("format: Y-m-d H:M:S"),
    )
"""


class Stock(models.Model):
    product = models.OneToOneField(
        ProductItem, related_name="stock", on_delete=models.PROTECT
    )
    unit = models.CharField(
        _("product unit"), max_length=20, help_text=_("required, max_len: 20")
    )
    initial_amount = models.PositiveIntegerField(
        _("initial amount of product"),
        default=0,
        help_text=_("required, default: 0"),
    )
    current_amount = models.PositiveIntegerField(
        _("current amount of product"),
        default=0,
        help_text=_("required, default: 0"),
    )
    items_sold = models.PositiveIntegerField(
        _("amount of product sold"),
        default=0,
        help_text=_("required, default: 0"),
    )
    created_at = models.DateTimeField(
        _("Stock item creation time"),
        auto_now_add=True,
        help_text=_("format: Y-m-d H:M:S"),
    )
    updated_at = models.DateTimeField(
        _("Stock item last update time"),
        auto_now=True,
        help_text=_("format: Y-m-d H:M:S"),
    )

    def add(self, value: int) -> None:
        if value >= MAX_AMOUNT_ADDED:
            raise TooBigToAdd(value)
        self.current_amount += value
        self.save()

    def subtract(self, value: int) -> None:
        if value > self.current_amount:
            raise NotEnoughProductLeft(self)
        self.current_amount -= value
        self.save()

    def __str__(self) -> str:
        return self.product_id


class Cart(models.Model):
    # maybe try: Cart.objects.select_related('customer)?
    class CartStatus(models.TextChoices):
        EMPTY = "empty"
        IN_PROGRESS = "in_progress"

    customer = models.OneToOneField(
        Customer,
        related_name="cart",
        on_delete=models.PROTECT,
        verbose_name=_("Cutomer"),
        help_text="required, customer instance",
    )
    status = models.CharField(
        _("Cart status"),
        max_length=20,
        choices=CartStatus.choices,
        default=CartStatus.EMPTY,
        help_text=_("required, default: empty"),
    )
    created_at = models.DateTimeField(
        _("cart creation time"),
        auto_now_add=True,
        help_text=_("format: Y-m-d H:M:S"),
    )
    updated_at = models.DateTimeField(
        _("cart last update time"),
        auto_now=True,
        help_text=_("format: Y-m-d H:M:S"),
    )

    def clear_out(self):
        self.items.all().delete()

    def __str__(self) -> str:
        return str(self.customer_id)


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name="Item in cart",
    )
    product = models.ForeignKey(
        ProductItem, on_delete=models.PROTECT, verbose_name=_("Product item")
    )
    _quantity = models.PositiveIntegerField(
        _("Product quantity"),
        validators=[MinValueValidator(1)],
        help_text=_("reqiured, positive integer"),
        default=1,
    )
    marked_for_order = models.BooleanField(
        _("Item selected to be ordered"),
        default=False,
        help_text=_("required, default: False"),
    )
    created_at = models.DateTimeField(
        _("cart_item creation time"),
        auto_now_add=True,
        help_text=_("format: Y-m-d H:M:S"),
    )
    updated_at = models.DateTimeField(
        _("cart_item last update time"),
        auto_now=True,
        help_text=_("format: Y-m-d H:M:S"),
    )

    def add_quantity(self, quantity: int) -> None:
        self._quantity += quantity
        self.save()

    # view behavior:
    # def add_cart_item(request, prod_id, cart_id, quantity=1):
    #   from django.utils.timezone import now

    #   try:
    #       cart_item, created = CartItem.objects.get_or_create(cart_id=cart_id, product_id=product_id)
    #       if created:
    #         cart_item.add_quantity(quantity)
    #         cart_item.updated_at = now()
    #   except IntegrityError as e:
    #       print('product_item or cart doesn\'t exist')
    #       return
    #   Cart.objects.filter(id=cart_id).update(created_at=now())
    #
    # or maybe need to fetch the product: ProductItem.objects.select_related('cart').get(id=prod_id)


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        CREATED = "created"
        PAID = "paid"
        PROCESSING = "processing"
        DELIVERY_READY = "delivery_ready"
        ON_DELIVERY = "on_delivery"
        DELIVERED = "delivered"
        FINISHED = "finished"
        CANCELED_BY_CUSTOMER = "canceled_by_customer"
        CANCELED_BY_SELLER = "canceled_by_seller"

    customer = models.ForeignKey(
        Customer, related_name="orders", on_delete=models.PROTECT
    )  # change to models.SET_DEFAULT
    items = models.ManyToManyField(
        CartItem,
        related_name="orders",
        help_text=_("Items from Cart included in Order"),
    )
    _status = models.CharField(
        _("Order status"),
        max_length=50,
        choices=OrderStatus.choices,
        default=OrderStatus.CREATED,
        help_text=_("required, default: created"),
    )
    # products = models.ManyToManyField(ProductItem, related_name="orders")
    created_at = models.DateTimeField(
        _("order creation time"),
        auto_now_add=True,
        help_text=_("format: Y-m-d H:M:S"),
    )
    updated_at = models.DateTimeField(
        _("order last update time"),
        auto_now=True,
        help_text=_("format: Y-m-d H:M:S"),
    )
    # status = ...
    # shipment_method = ...
    # payment_method = ...
    total_sum = models.PositiveIntegerField(
        _("order sum without discounts"),
        help_text=_("required, positive number"),
    )
    total_discount = models.PositiveIntegerField(
        _("sum of discounts"),
        blank=True,
        null=True,
        help_text=_("optional, positive number"),
    )
    final_sum = models.PositiveIntegerField(
        _("order sum with discounts"), help_text=_("required, positive number")
    )
    # delivery_info = ...  # FK DELIVERY

    def from_cart(self, cart_id: int):
        if cart_items := CartItem.objects.filter(cart_id=cart_id).filter(
            marked_for_order=True
        ):
            self.items.add(*cart_items)
        else:
            raise EmptyQuerySet(
                f"No items ready for order in Cart # {cart_id}"
            )

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        if stat := getattr(self.OrderStatus, value, None):
            self._status = stat
        else:
            raise ValueError(f"{value} is not a valid choice fo OrderStatus")


class Comment(models.Model):
    pass


class Foo(models.Model):
    label = models.CharField(_("label"), max_length=100)
    attrs = models.JSONField(_("attrs"))
