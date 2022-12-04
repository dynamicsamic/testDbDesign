import random

import factory
from dbexample import models
from django.contrib.auth import get_user_model
from faker import Faker

fake = Faker()
User = get_user_model()


PRODUCT_TYPE_NUM = 5
ATTRIBUTE_NUM = 7
USER_NUM = CATEGORY_NUM = VENDOR_NUM = PRODUCT_NUM = 10
BRAND_NUM = 14
PRODUCT_VERSION_NUM = 30

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

# ATTR_VALUES = [
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
ATTR_VALUES = [
    "attr_value1",
    "attr_value2",
    "attr_value3",
    "attr_value4",
    "attr_value5",
]


# def random_seq(n: int, l: int):
#    "n - number of items; l - limit"
#    return [random.randint(1, l) for _ in range(n)]


def randomize(seq, n):
    return random.sample(seq, k=random.randint(1, n))


def set_random_attrs(obj):
    """A helper function to be passed to LazyAttribute of a factory."""
    return {
        attr.name: random.choice(ATTR_VALUES)
        for attr in obj.product.p_type.attributes.all()
    }


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda i: f"user{i}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@hello.py")
    password = "hello"


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Customer

    user = factory.Iterator(User.objects.all())
    status = factory.Sequence(
        lambda _: random.choice(models.Customer.CustomerStatus.values)
    )
    phone_number = factory.Sequence(lambda _: fake.phone_number())


class ProductAttributeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductAttribute

    name = factory.Sequence(lambda i: f"Attribute {i}")
    # name = factory.Iterator(attribute_names)


class ProductTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductType

    name = factory.Sequence(lambda n: f"Product Type {n}")
    logo = factory.Sequence(lambda i: f"logo_{i}.png")

    @factory.post_generation
    def attributes(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        if extracted:
            extracted = randomize(extracted, ATTRIBUTE_NUM)
            for attribute in extracted:
                self.attributes.add(attribute)


class ProductCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductCategory

    name = factory.Sequence(lambda i: f"category {i}")


class VendorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Vendor

    name = factory.Sequence(lambda i: f"Vendor {i}")
    description = fake.text()


class BrandFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Brand

    name = factory.Sequence(lambda i: f"brand_{i}")
    description = fake.text()
    logo = factory.Sequence(lambda i: f"logo_{i}.png")
    vendor = factory.Iterator(models.Vendor.objects.all())


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Product

    #    p_type = factory.Iterator(models.ProductType.objects.all())
    p_type = factory.Sequence(
        lambda _: random.choice(models.ProductType.objects.all())
    )
    # brand = factory.Iterator(models.Brand.objects.all())
    brand = factory.Sequence(
        lambda _: random.choice(models.Brand.objects.all())
    )
    web_id = factory.Sequence(lambda i: f"product_web_id_{i}")
    # slug = factory.Sequence(lambda i: f"product_slug_{i}")
    name = factory.Sequence(lambda i: f"product{i}")
    # description = fake.text()
    description = factory.Faker("sentence", nb_words=9)
    is_active = factory.Sequence(
        lambda _: bool(*random.choices((1, 0), weights=(0.8, 0.2)))
    )

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        if extracted:
            extracted = randomize(extracted, CATEGORY_NUM)
            for category in extracted:
                self.categories.add(category)


class ProductVersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductVersion

    product = factory.Iterator(models.Product.objects.all())
    name = factory.Sequence(lambda i: f"product_version{i}")
    # sku = factory.Sequence(lambda i: f"110_{i}")
    attrs = factory.LazyAttribute(set_random_attrs)
    regular_price = factory.Sequence(
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
    _view_count = factory.Sequence(lambda _: fake.pyint())
    made_in = factory.Sequence(lambda _: fake.country())

    @factory.post_generation
    def favorited_by(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        if extracted:
            extracted = randomize(extracted, USER_NUM)
            for user in extracted:
                self.favorited_by.add(user)


class StockFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Stock

    p_version = factory.Iterator(models.ProductVersion.objects.all())
    unit = "pcs"
    amount = factory.Sequence(lambda _: fake.pyint(max_value=999))


class CartFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Cart

    customer = factory.Iterator(models.Customer.objects.all())
