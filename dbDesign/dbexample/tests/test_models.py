from django.core.exceptions import ValidationError
from django.test import TestCase

from ..exceptions import NotEnoughProductLeft, TooBigToAdd
from ..models import MAX_AMOUNT_ADDED
from .fixtures import factories

PRODUCT_TYPE_NUM = 5
ATTRIBUTE_NUM = 7
CATEGORY_NUM = VENDOR_NUM = PRODUCT_SET_NUM = 10
BRAND_NUM = 14
PRODUCT_ITEM_NUM = 30


class ModelsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendors = factories.VendorFactory.create_batch(VENDOR_NUM)
        cls.brands = factories.BrandFactory.create_batch(BRAND_NUM)
        cls.attributes = factories.ProductAttributeFactory.create_batch(
            ATTRIBUTE_NUM
        )
        cls.p_types = factories.ProductTypeFactory.create_batch(
            PRODUCT_TYPE_NUM, attribute_set=cls.attributes
        )
        cls.categories = factories.ProductCategoryFactory.create_batch(
            CATEGORY_NUM
        )
        cls.product_sets = factories.ProductSetFactory.create_batch(
            PRODUCT_SET_NUM, categories=cls.categories
        )
        cls.product_items = factories.ProductItemFactory.create_batch(
            PRODUCT_ITEM_NUM
        )
        cls.stock = factories.StockFactory.create_batch(PRODUCT_ITEM_NUM)

    def test_stock_fails_to_set_more_than_highest_num(self):
        """Raises specific error when trying to set more than allowed"""
        stock = self.stock[0]
        with self.assertRaises(ValidationError):
            stock.set(MAX_AMOUNT_ADDED + 1)

    def test_stock_fails_to_add_more_than_highest_num(self):
        """Raises specific error when trying to add more than allowed"""
        stock = self.stock[0]
        with self.assertRaises(TooBigToAdd):
            stock.add(MAX_AMOUNT_ADDED + 1)

    def test_stock_fails_to_deduct_more_than_available(self):
        """Raises specific error when trying to deduct more than current amount"""
        stock = self.stock[0]
        with self.assertRaises(NotEnoughProductLeft):
            stock.deduct(stock.amount + 1)

    def test_stock_fails_operating_negative_numbers(self):
        stock = self.stock[0]
        with self.assertRaises(ValidationError):
            stock.deduct(-1)
            stock.add(-1)
            stock.set(-1)
