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
    # name = fake.lexify('prod_cat_name_????????')
    # slug = fake.lexify('prod_cat_slug_????????')


class ProductSetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductSet

    web_id = factory.Sequence(lambda i: f"prodset_web_id_{i}")
    slug = fake.lexify(text="productset_slug_????????")
    name = fake.lexify(text="productset_name_????????")
    description = fake.text()
    is_active = fake.boolean()
    created_at = fake.date_this_decade()
    updated_at = fake.date_this_decade()

    @factory.post_generation
    def category(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        if extracted:
            for category in extracted:
                self.categories.add(category)


register(ProductCategoryFactory)
register(ProductSetFactory, _name="productset_factory")
