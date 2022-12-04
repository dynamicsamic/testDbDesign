from typing import Any, Optional

from dbexample.tests.fixtures import factories
from django.core.management import call_command
from django.core.management.base import BaseCommand

# from ....dbexample.tests.fixtures import factories

PRODUCT_TYPE_NUM = 5
ATTRIBUTE_NUM = 7
USER_NUM = CATEGORY_NUM = VENDOR_NUM = PRODUCT_NUM = 10
BRAND_NUM = 14
PRODUCT_VERSION_NUM = 30


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        call_command("makemigrations")
        call_command("migrate")
        users = factories.UserFactory.create_batch(USER_NUM)
        customers = factories.CustomerFactory.create_batch(USER_NUM)
        for user in users:
            user.set_password(user.password)
            user.save(update_fields=("password",))

        factories.VendorFactory.create_batch(VENDOR_NUM)
        factories.BrandFactory.create_batch(BRAND_NUM)

        attributes = factories.ProductAttributeFactory.create_batch(
            ATTRIBUTE_NUM
        )
        factories.ProductTypeFactory.create_batch(
            PRODUCT_TYPE_NUM, attributes=attributes
        )
        categories = factories.ProductCategoryFactory.create_batch(
            CATEGORY_NUM
        )

        factories.ProductFactory.create_batch(
            PRODUCT_NUM, categories=categories
        )
        factories.ProductVersionFactory.create_batch(
            PRODUCT_VERSION_NUM, favorited_by=customers
        )
        factories.StockFactory.create_batch(PRODUCT_VERSION_NUM)
        factories.CartFactory.create_batch(USER_NUM)
