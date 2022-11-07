import random

import factory
from django.test import TestCase
from faker import Faker

from .. import models

fake = Faker()

NUM_ATTRIBUTES = 7
NUM_CATEGORIES = 10
attribute_names = [
    "cpu",
    "storage",
    "RAM",
    "display",
    "color",
    "graphics",
    "capacity",
    "interface",
    "form-factor",
]

# attr_values = [
#    "Intel Core i7",
#    "AMD Ryzen 5",
#    "256 GB SSD",
#    "1 TB HDD",
#    "512 GB HDD",
#    "6 GB",
#    "8 GB",
#    "13.1 Full HD",
#    "17.3 4K Ultra HD",
#    "NVIDIA GeForce GTX 1060",
# ]
attr_values = [
    "attr_value1",
    "attr_value2",
    "attr_value3",
    "attr_value4",
    "attr_value5",
]


def random_seq(n: int, l: int):
    "n - number of items; l - limit"
    return [random.randint(1, l) for _ in range(n)]


def randomize(seq, n):
    return random.sample(seq, k=random.randint(1, n))


class ProductAttributeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductAttribute

    name = factory.Sequence(lambda i: f"attribute{i}")
    # name = factory.Iterator(attribute_names)


class ProductTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductType

    name = factory.Sequence(lambda n: f"prod_type{n}")
    logo = factory.Sequence(lambda i: f"logo_{i}.png")

    @factory.post_generation
    def attribute_set(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        if extracted:
            extracted = randomize(extracted, NUM_ATTRIBUTES)
            for attribute in extracted:
                self.attribute_set.add(attribute)


class ProductCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductCategory

    name = factory.Sequence(lambda name: f"prod_cat_name_{name}")
    slug = factory.Sequence(lambda slug: f"prod_cat_name_{slug}")
    # name = fake.lexify("prod_cat_name_????????")
    # slug = fake.lexify("prod_cat_slug_????????")


class VendorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Vendor

    name = factory.Sequence(lambda i: f"vendor_{i}")
    description = fake.text()


class BrandFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Brand

    name = factory.Sequence(lambda i: f"brand_{i}")
    description = fake.text()
    logo = factory.Sequence(lambda i: f"logo_{i}.png")
    vendor = factory.Iterator(models.Vendor.objects.all())


class ProductSetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductSet

    p_type = factory.Iterator(models.ProductType.objects.all())
    brand = factory.Iterator(models.Brand.objects.all())
    web_id = factory.Sequence(lambda i: f"product_set_web_id_{i}")
    slug = factory.Sequence(lambda i: f"product_set_slug_{i}")
    name = factory.Sequence(lambda i: f"product_set{i}")
    # description = fake.text()
    description = factory.Faker("sentence", nb_words=9)
    is_active = fake.boolean()
    created_at = fake.date_this_decade()
    updated_at = fake.date_this_decade()

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        if extracted:
            extracted = randomize(extracted, NUM_CATEGORIES)
            for category in extracted:
                self.categories.add(category)


def set_random_attrs(obj):
    """A helper function to be passed to LazyAttribute of a factory."""
    return {
        attr.name: random.choice(attr_values)
        for attr in obj.product_set.p_type.attribute_set.all()
    }


class ProductItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductItem

    product_set = factory.Iterator(models.ProductSet.objects.all())
    product_name = factory.Sequence(lambda i: f"product_item{i}")
    sku = factory.Sequence(lambda i: f"110_{i}")
    attrs = factory.LazyAttribute(set_random_attrs)
    price = factory.Sequence(
        lambda _: fake.pydecimal(
            left_digits=random.randint(1, 7), right_digits=2, positive=True
        )
    )
    discount = factory.Sequence(
        lambda _: fake.pyint(min_value=0, max_value=99)
    )
    # discount = fake.pyint(min_value=0, max_value=99)
    #    is_active = factory.Iterator([True, True, True, False, True])
    is_active = factory.Sequence(
        lambda _: bool(*random.choices((1, 0), weights=(0.8, 0.2)))
    )
    made_in = factory.Sequence(lambda _: fake.country())


class TestFoo(TestCase):
    def test_sample(self):
        vendors = VendorFactory.create_batch(10)
        brands = BrandFactory.create_batch(13)
        attributes = ProductAttributeFactory.create_batch(NUM_ATTRIBUTES)
        p_types = ProductTypeFactory.create_batch(5, attribute_set=attributes)
        # for p in models.ProductType.objects.all():
        #    print(p.attribute_set.all())
        # p_types = ProductTypeFactory.create_batch(
        #    5, attribute_set=list(models.ProductAttribute.objects.all())
        # )
        categories = ProductCategoryFactory.create_batch(NUM_CATEGORIES)
        product_sets = ProductSetFactory.create_batch(
            10, categories=categories
        )
        product_items = ProductItemFactory.create_batch(20)
        for p_item in product_items:
            print(p_item.made_in)
            # print(p_item.attrs)
            # print(p_item.product_set)
        # print(models.Vendor.objects.all())
        # for brand in models.Brand.objects.all():
        #    print(brand.vendor)
        # self.assertEquals(len(categories), 10)
