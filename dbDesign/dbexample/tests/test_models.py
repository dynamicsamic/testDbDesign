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


class DataFactoryMixin:
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
        cls.stockpile = factories.StockFactory.create_batch(PRODUCT_ITEM_NUM)


class StockModelTestCase(DataFactoryMixin, TestCase):
    def setUp(self):
        self.VALID_STOCK_AMOUNT = 20
        self.stock = self.stockpile[0]

    def test_stock_set_valid_amount_success(self):
        self.stock.set(self.VALID_STOCK_AMOUNT)
        self.stock.refresh_from_db()
        self.assertEquals(self.stock.amount, self.VALID_STOCK_AMOUNT)

    def test_stock_add_valid_amount_success(self):
        initial_amount = self.stock.amount
        self.stock.add(self.VALID_STOCK_AMOUNT)
        self.stock.refresh_from_db()
        self.assertEquals(
            self.stock.amount, initial_amount + self.VALID_STOCK_AMOUNT
        )

    def test_stock_deduct_valid_amount_success(self):
        initial_amount = self.stock.amount
        self.stock.deduct(self.VALID_STOCK_AMOUNT)
        self.stock.refresh_from_db()
        self.assertEquals(
            self.stock.amount, initial_amount - self.VALID_STOCK_AMOUNT
        )

    def test_stock_set_too_big_value_fails(self):
        """Raises specific error when trying to set more than allowed"""
        with self.assertRaises(ValidationError):
            self.stock.set(MAX_AMOUNT_ADDED + 1)

    def test_stock_add_too_big_value_fails(self):
        """Raises specific error when trying to add more than allowed"""
        with self.assertRaises(TooBigToAdd):
            self.stock.add(MAX_AMOUNT_ADDED + 1)

    def test_stock_deduct_more_than_available_fails(self):
        """Raises specific error when trying to deduct more than current amount"""
        with self.assertRaises(NotEnoughProductLeft):
            self.stock.deduct(self.stock.amount + 1)

    def test_stock_methods_with_negative_numbers_fails(self):
        with self.assertRaises(ValidationError):
            self.stock.deduct(-1)
            self.stock.add(-1)
            self.stock.set(-1)


class UserModelTestCase(TestCase):
    def test_smth(self):
        user = factories.UserFactory.create()
        customer = factories.CustomerFactory.create()
        print(user.email, customer.email)
