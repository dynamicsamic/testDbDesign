from django.db import models
from django.utils.translation import gettext_lazy as _


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


class Agent(models.Model):
    name = models.CharField(
        _("name of the agent/partner"),
        max_length=150,
        unique=True,
        help_text=_("required, max_len: 150"),
    )
    adress = models.ForeignKey(
        Address, related_name="agents", on_delete=models.PROTECT
    )

    class Meta:
        abstract = True


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


class ProductType(models.Model):
    name = models.CharField(
        _("type of product"),
        max_length=150,
        unique=True,
        help_text=_("required, max_len: 150"),
    )


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
        return f"ProductCategory({self.name})"


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
        return f"ProductSet({self.name})"
