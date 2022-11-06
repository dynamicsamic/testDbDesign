import datetime as dt
from decimal import Decimal
from typing import Any, Mapping

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from .exceptions import EmptyQuerySet, NotEnoughProductLeft, TooBigToAdd
from .utils import decimalize

MAX_AMOUNT_ADDED = 10000


class CustomerManager(models.Manager):
    def create(self, **kwargs):
        """Create an empty cart when creating a customer."""
        customer = super().create(**kwargs)
        Cart.objects.create(customer=customer)
        return customer

    def get_queryset(self) -> QuerySet:
        """Fetch user data when querying for customer."""
        return super().get_queryset().select_related("user")


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
        ACTIVATED = "activated"
        FROZEN = "frozen"
        ARCHIVED = "archived"

    objects = CustomerManager()

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


class ProductType(models.Model):
    name = models.CharField(
        _("type of product"),
        max_length=150,
        unique=True,
        help_text=_("required, max_len: 150"),
    )
    logo = models.CharField(_("replace this to imagefield"), max_length=30)
    attribute_set = models.ManyToManyField(
        ProductAttribute,
        related_name="product_types",
        through="ProductTypeToAttributeLinkTable",
    )

    def __str__(self):
        return self.name


class ProductTypeToAttributeLinkTable(models.Model):
    """Link table for product type and attribute values."""

    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT)
    attr = models.ForeignKey(
        ProductAttribute,
        on_delete=models.PROTECT,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product_type", "attr"],
                name="unique_product_type_attr",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product_type_id}: {self.attr_id}"


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


class ProductItemManager(models.Manager):
    def create(self, **kwargs):
        # product_name
        # kwargs.update({'product_name'})
        p_set = kwargs.get("product_set")
        attrs = kwargs.get("attrs")
        if p_set:
            if attrs:
                p_name = (
                    p_set.name
                    + " "
                    + " ".join([value for value in attrs.values()])
                )
            else:
                p_name = p_set.name
            kwargs.update({"product_name": p_name})
        product_item = super().create(**kwargs)
        Stock.objects.create(product=product_item, units="pcs")
        return product_item

        # obj = super().create(**kwargs)
        # p_name = obj.product_set.name
        # full_name = p_name + " " + " ".join([attr.value for attr in obj.attrs])
        # obj.product_name = full_name
        # obj.save()
        # return obj


class ProductItem(models.Model):
    """Particular item of product with specific attributes."""

    # think about favorites
    product_set = models.ForeignKey(
        ProductSet, related_name="items", on_delete=models.CASCADE
    )
    favorited_by = models.ManyToManyField(
        Customer,
        related_name="favorites",
        help_text=_("optional, customers liked the product"),
    )
    product_name = models.CharField(
        _("Product name"),
        max_length=150,
        help_text=_("optional, max_len: 150"),
        blank=True,
        # null=True,
    )
    sku = models.CharField(
        _("stock keeping unit"),
        max_length=20,
        help_text="required, max_len: 20",
    )
    attrs = models.JSONField(
        _("Attributes for product item "),
        help_text=_("required: dict of attr:vaue pairs"),
    )
    # images = models.ForeignKey(
    #    ImageSet, related_name="product_items", on_delete=models.SET_DEFAULT
    # )
    _price = models.DecimalField(
        _("Product item price"),
        max_digits=9,
        decimal_places=2,
        help_text=_("required, max_price: 9_999_999.99"),
    )
    discount = models.PositiveSmallIntegerField(
        _("Discount rate (integer)"),
        default=0,
        help_text=_("required, default: 0"),
        validators=[MaxValueValidator(99)],
    )
    # final_price = models.DecimalField(
    #    _("Product item final price"),
    #    max_digits=9,
    #    decimal_paces=2,
    #    blank=True,
    #    null=True,
    #    help_text=_("set automatically"),
    # )
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

    objects = ProductItemManager()

    def __str__(self):
        return self.product_name

    @property
    def views(self) -> int:
        return self._view_count

    @property
    def price(self) -> Decimal:
        return self._price

    @price.setter
    def price(self, value) -> None:
        try:
            self._price = Decimal(format(value, ".2f"))
            self.save(update_fields=("_price",))
        except ValueError:
            pass

    @property
    @decimalize()
    def discounted_price(self) -> Decimal:
        price = float(self._price) * ((100 - self.discount) / 100)
        return round(price, 2)

    def increment_view_count(self) -> None:
        self._view_count += 1
        self.save(update_fields=("_view_count",))

    def to_dict(self) -> dict:
        return {
            "product_name": self.product_name,
            "sku": self.sku,
            "regular_price": self._price.to_eng_string(),
            "discount": self.discount,
            "final_price": self.discounted_price.to_eng_string(),
        }


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

    def add(self, value: int, commit: bool = True) -> None:
        if value >= MAX_AMOUNT_ADDED:
            raise TooBigToAdd(value)
        self.current_amount += value
        if commit:
            self.save(update_fields=("current_amount",))

    def deduct(self, value: int, commit: bool = True) -> None:
        if value > self.current_amount:
            raise NotEnoughProductLeft(self)
        self.current_amount -= value
        if commit:
            self.save(update_fields=("current_amount",))

    def available(self, amount: int) -> bool:
        return self.current_amount >= amount

    def __str__(self) -> str:
        return str(self.product_id)


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
        """Clean the cart."""
        self.items.all().delete()
        self.status = self.CartStatus.EMPTY
        self.save(update_fields=("status",))

    def get_initial_sum(self) -> Decimal:
        """Get sum of all items in cart before discount applied."""
        if res := self.items.aggregate(initial=Sum("regular_price")).get(
            "initial"
        ):
            return res
        return Decimal("0.00")
        # return round(
        #    *CartItem.objects.filter(cart_id=self.id)
        #    .aggregate(Sum("regular_price"))
        #    .values(),
        #    2,
        # )

    def get_total_sum(self) -> Decimal:
        """Get sum of all items in cart after dicsount added."""
        if res := self.items.aggregate(total=Sum("final_price")).get("total"):
            return res
        return Decimal("0.00")
        # return round(
        #    *CartItem.objects.filter(cart_id=self.id)
        #    .aggregate(Sum("final_price"))
        #    .values(),
        #    2,
        # )

    def get_total_discount(self) -> Decimal:
        """Get sum of total cart discount."""
        if res := self.items.aggregate(
            discount=Sum("regular_price") - Sum("final_price")
        ).get("discount"):
            return res
        return Decimal("0.00")

    def __str__(self) -> str:
        return str(self.customer_id)


class CartItemManager(models.Manager):
    def create(self, **kwargs: Mapping[str, Any]):
        """Check if a product item is already in the cart.
        If it's there - increase the quantity.
        If it's not - create a new cart item.
        """
        cart = kwargs.get("cart")
        product = kwargs.get("product")
        quantity = kwargs.get("quantity", 1)
        try:
            cart_item = self.model.objects.get(cart=cart, product=product)
            cart_item.add_quantity(quantity)
        except self.model.DoesNotExist:
            cart_item = super().create(**kwargs)
        except Exception as e:
            print(f"An unexpected error occured: {e}")
            return
        if cart.status == Cart.CartStatus.EMPTY:
            cart.status = Cart.CartStatus.IN_PROGRESS
            cart.save(update_fields=("status",))
        return cart_item

    #   if product := kwargs.get("product"):
    #       kwargs.update(
    #           {
    #               "product_name": product.product_name,
    #               "price": product.discounted_price,
    #           }
    #       )


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name="Item in cart",
    )
    product = models.ForeignKey(
        ProductItem,
        related_name="in_cart",
        on_delete=models.PROTECT,
        verbose_name=_("Product item"),
    )
    product_name = models.CharField(
        _("Product name"),
        max_length=150,
        help_text=_("optional, max_len: 150"),
        blank=True,
        null=True,
    )
    sku = models.CharField(
        _("stock keeping unit"),
        max_length=20,
        help_text="optional, max_len: 20",
        blank=True,
        null=True,
    )
    quantity = models.PositiveIntegerField(
        _("Product quantity"),
        validators=[MinValueValidator(1)],
        help_text=_("reqiured, positive integer"),
        default=1,
    )
    regular_price = models.DecimalField(
        _("Product item price"),
        max_digits=9,
        decimal_places=2,
        help_text=_("optional, max_price: 9_999_999.99"),
        blank=True,
        null=True,
    )
    discount = models.PositiveSmallIntegerField(
        _("Discount rate (integer)"),
        default=0,
        help_text=_("optional, default: 0"),
        validators=[MaxValueValidator(99)],
        blank=True,
        null=True,
    )
    final_price = models.DecimalField(
        _("Discounted cart item price"),
        max_digits=9,
        decimal_places=2,
        help_text=_("optional, max_price: 9_999_999.99"),
        blank=True,
        null=True,
    )
    # is_active ??
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

    objects = CartItemManager()

    def save(self, *args, **kwargs) -> None:
        """Update cart info each time a cart item updated."""
        super().save(*args, **kwargs)
        self.cart.save(update_fields=("updated_at",))

    @classmethod
    def from_product_item(
        cls, customer_id: int, product_item_id: int, **kwargs: dict
    ):
        """Create CartItem from ProductItem.
        Prevent creating cart items from inactive products
        and products that don't have enough stock items.
        Fetch stock data along with the product item
        to prevent additional db queries.
        """
        try:
            cart = Cart.objects.get(customer_id=customer_id)
            product_item = ProductItem.objects.select_related("stock").get(
                id=product_item_id
            )
        except (Cart.DoesNotExist, ProductItem.DoesNotExist) as e:
            print(e)
            raise
        if not product_item.is_active:
            raise ValidationError(
                _("Inactive products can't be added to cart")
            )
        if not product_item.stock.available(kwargs.get("quantity", 1)):
            raise ValidationError(_("Not enough product in stock"))
            # maybe need to deduct from stock to reserve items for order
            # but then need to keep notice of cleansing the cart periodically
        product_data = product_item.to_dict()
        kwargs.update(product_data)
        cart_item = cls.objects.create(
            cart=cart, product=product_item, **kwargs
        )

        return cart_item

    def to_dict(self) -> dict:
        return {
            # "cart": self.cart,
            "product": self.product,
            "product_name": self.product_name,
            "sku": self.sku,
            "quantity": self.quantity,
            # "regular_price": self.regular_price,
            # "discount": self.discount,
            "price": self.final_price,
            "sum": self.get_final_sum()
            # "marked_for_order": self.marked_for_order,
        }

    def add_quantity(self, quantity: int) -> None:
        self.quantity += quantity
        self.save(update_fields=("quantity",))

    @decimalize()
    def get_final_sum(self) -> Decimal:
        return self.final_price * self.quantity

    def mark_for_order(self) -> None:
        self.marked_for_order = True
        self.save(update_fields=("marked_for_order",))

    def unmark_for_order(self) -> None:
        self.marked_for_order = False
        self.save(update_fields=("marked_for_order",))

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
        PENDING = "pending"
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
    _status = models.CharField(
        _("Order status"),
        max_length=50,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        help_text=_("required, default: pending"),
    )
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
    # shipment_method = ...
    # payment_method = ...
    total_sum = models.PositiveIntegerField(
        _("order sum without discounts"),
        help_text=_("required, positive number"),
        blank=True,
        null=True,
    )
    total_discount = models.PositiveIntegerField(
        _("sum of discounts"),
        blank=True,
        null=True,
        help_text=_("optional, positive number"),
    )
    final_sum = models.PositiveIntegerField(
        _("order sum with discounts"),
        help_text=_("required, positive number"),
        blank=True,
        null=True,
    )
    # delivery_info = ...  # FK DELIVERY

    # def from_cart(self, cart_id: int):
    #    if cart_items := CartItem.objects.filter(cart_id=cart_id).filter(
    #        marked_for_order=True
    #    ):
    #        self.items.add(*cart_items)
    #    else:
    #        raise EmptyQuerySet(
    #            f"No items ready for order in Cart # {cart_id}"
    #        )

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        if stat := getattr(self.OrderStatus, value.upper(), None):
            self._status = stat
        else:
            raise ValueError(f"{value} is not a valid choice for OrderStatus")

    def get_total_sum(self) -> Decimal:
        if res := self.items.aggregate(total=Sum("sum")).get("total"):
            return res
        return Decimal("0.00")

    def get_total_discount(self) -> float:
        # return round(
        #    OrderItem.objects.filter(order_id=self.id).aggregate(Sum("sum")), 2
        # )
        pass

    def cancel(self):
        for item in self.items.all():
            item.revert()
        self.status = "canceled_by_seller"
        self.save(update_fields=("_status",))

    @classmethod
    def create_from_cart(cls, customer: Customer):
        order, _ = cls.objects.get_or_create(
            customer=customer, _status=cls.OrderStatus.PENDING
        )
        cart = Cart.objects.filter(
            customer_id=customer.id, status=Cart.CartStatus.IN_PROGRESS
        ).first()
        cart_items = cart.items.all()
        for item in cart_items:
            if item.marked_for_order:
                OrderItem.from_cart_item(order, item)

        order.final_sum = order.get_total_sum()
        order.save(update_fields=("final_sum",))


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name=_("Customer Order"),
    )
    product = models.ForeignKey(
        ProductItem,
        related_name="order_items",
        on_delete=models.PROTECT,
        verbose_name="Ordered product",
        blank=True,
        null=True,
    )
    product_name = models.CharField(
        _("Product name"),
        max_length=150,
        help_text=_("required, max_len: 150"),
        blank=True,
        null=True,
    )
    sku = models.CharField(
        _("stock keeping unit"),
        max_length=20,
        help_text="optional, max_len: 20",
        blank=True,
        null=True,
    )
    quantity = models.PositiveIntegerField(
        _("Quantity of the ordered product"),
        default=1,
        help_text=_("optional: default 1"),
        blank=True,
        null=True,
    )
    price = models.DecimalField(
        _("Final price of ordered product"),
        max_digits=9,
        decimal_places=2,
        help_text=_("optional, max_price: 9 999 999.99"),
        blank=True,
        null=True,
    )
    sum = models.DecimalField(
        _("Final sum of ordered product"),
        max_digits=12,
        decimal_places=2,
        help_text=_("optional, max_sum: 9 999 999 999.99"),
        blank=True,
        null=True,
    )

    def revert(self) -> None:
        """Restore the quantity of stock units when the order is canceled.
        Set quantity item quantity to 0.
        """
        stock = Stock.objects.filter(product_id=self.product_id).first()
        stock.add(self.quantity, commit=False)
        stock.items_sold -= self.quantity
        stock.save(
            update_fields=(
                "current_amount",
                "items_sold",
            )
        )
        self.quantity = 0
        self.save(update_fields=("quantity",))

    @classmethod
    def from_cart_item(cls, order: Order, cart_item: CartItem, **kwargs):
        """Create an order item from a cart item."""
        data = cart_item.to_dict()
        if product := data.get("product"):
            stock = product.stock
            # quantity = data.get("quantity", 1)
            # if not stock.available(quantity):
            #    raise ValidationError(_("Not enough product in stock"))
            # stock.deduct(quantity)
            try:
                stock.deduct(quantity := data.get("quantity", 1), commit=False)
            except NotEnoughProductLeft as e:
                print(f"{e(quantity)}")
                raise
            stock.items_sold += quantity
            stock.save(
                update_fields=(
                    "current_amount",
                    "items_sold",
                )
            )
        kwargs.update(data)
        cart_item.delete()
        return cls.objects.create(order=order, **kwargs)


class Comment(models.Model):
    pass


class Foo(models.Model):
    class MAN(models.Manager):
        def create(self, **kwargs):
            kwargs.update({"label": "FFFF"})
            obj = super().create(**kwargs)
            # obj.label = "FFFFFF"
            # obj.save()
            return obj

    objects = MAN()

    label = models.CharField(_("label"), max_length=100)
    attrs = models.JSONField(_("attrs"))
