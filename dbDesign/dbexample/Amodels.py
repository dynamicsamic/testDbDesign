from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class BaseUser(AbstractUser):
    email = models.EmailField(_('email adress'), unique=True)

    class Meta:
        abstract = True

class Customer(BaseUser):
    pass

class Employee(BaseUser):
    pass

class Address(models.Model):
    pass


class Agent(models.Model):
    name = models.CharField()
    adress = models.ForeignKey(Address)

    class Meta:
        abstract = True

class Supplier(Agent):
    pass


class Brand(models.Model):
    name = models.CharField()
    supplier = models.ForeignKey(Supplier)


class ImageSet(models.Model):
    name = models.CharField()


class Image(models.Model):
    image_set = models.ForeignKey(ImageSet, related_name='images', on_delete=models.CASCADE)
    file = models.ImageField()


class ProductCategory(models.Model):
    name = models.CharField()
    image = models.ImageField()


class ProductSet(models.Model):
    name = models.CharField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField()
    is_active = models.BooleanField()
    brand = models.ForeignKey(Brand, 'product_sets', on_delete=models.PROTECT)
    image_set = models.ForeignKey(ImageSet, related_name='product_sets', on_delete=models.SET_DEFAULT)
    category = models.ForeignKey(ProductCategory, related_name='product_sets', on_delete=models.PROTECT)


class ProductItem(models.Model):
    sku = models.CharField()
    product_set = models.ForeignKey(
        ProductSet, related_name='products',
        on_delete=models.CASCADE)
    retail_price = models.DecimalField()
    discount_price = models.DecimalField()
    attributes = models.ManyToManyField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField()
    is_active = models.BooleanField()






