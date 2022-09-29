import factory
import pytest
from faker import Faker
from pytest_factoryboy import register

fake = Faker()

from dbexample import models

class ProductCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductCategory

    name = factory.Sequence(lambda name: f"prod_cat_name_{name}")
    slug = factory.Sequence(lambda slug: f"prod_cat_name_{slug}")
    #name = fake.lexify('prod_cat_name_????????')
    #slug = fake.lexify('prod_cat_slug_????????')

register(ProductCategoryFactory)
