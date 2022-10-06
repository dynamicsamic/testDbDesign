from django.db import models
from django.db.models.manager import Manager
from django.utils.translation import gettext_lazy as _


class ManagerAutoIncrementViewCount(Manager):
    def get(self, *args, **kwargs):
        if result := super().get(*args, **kwargs):
            result.views += 1
            result.save()
            return result


class ViewsCountAutoIncrementMixin:
    def get(self, *args, **kwargs):
        if result := super().get(*args, **kwargs):
            if not hasattr(result, "view_count"):
                raise AttributeError(
                    _(
                        f"Instance {result.__class__.__name__} should have `view_count` attribute"
                    )
                )
            result.view_count += 1
            result.save()
            return result

    def get_or_create(self, defaults=None, **kwargs):
        result = super().get_or_create(defaults, **kwargs)
        obj, created = result
        if not created:
            if not hasattr(result, "view_count"):
                raise AttributeError(
                    _(
                        f"Instance {result.__class__.__name__} should have `view_count` attribute"
                    )
                )
            obj.view_count += 1
            obj.save()
            obj.refresh_from_db()
            return obj, created
        return result


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


class Brand(models.Model):
    name = models.CharField(
        _("brand name"),
        max_length=150,
        unique=True,
        help_text=_("required, max_len: 150"),
    )
    supplier = models.ForeignKey(
        Supplier,
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
    name = models.CharField(
        _("product item attribute name"),
        max_length=150,
        unique=True,
        help_text=_("required, max_len: 150"),
    )

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    attr = models.ForeignKey(
        ProductAttribute, related_name="values", on_delete=models.PROTECT
    )
    value = models.CharField(
        _("attribute value"),
        max_length=255,
        unique=True,
        help_text=_("required, max_length: 255"),
    )

    def __str__(self):
        return f"{self.attr}: {self.value}"


class ProductItem(models.Model):
    """Particular item of product with specific attributes."""

    # class CustomManager(ViewsCountAutoIncrementMixin, Manager):
    #    pass

    # objects = CustomManager()
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
        return f"{self.product_set.name}: {self.sku}"

    @property
    def views(self):
        return self._view_count

    def increment_view_count(self):
        self._view_count += 1
        self.save()


class ProductToAttributeLinkTable(models.Model):
    """Link table for product items and attribute values."""

    product_item = models.ForeignKey(ProductItem, on_delete=models.PROTECT)
    attr_values = models.ForeignKey(
        ProductAttributeValue,
        on_delete=models.PROTECT,
    )

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

    def add(self, value: int):
        self.current_amount += value

    def subtract(self, value: int):
        self.current_amount -= value


class Comment(models.Model):
    pass
