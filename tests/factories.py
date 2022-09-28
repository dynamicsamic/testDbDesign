import factory
import pytest
from faker import Faker
from pytest_factoryboy import register

fake = Faker()

from dbexample import models

class ProductCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductCategory

    name = fake.lexify('prod_cat_name_????????')
    slug = fake.lexify('prod_cat_slug_????????')

register(ProductCategoryFactory)
