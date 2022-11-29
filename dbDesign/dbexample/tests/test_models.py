import random
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, reset_queries
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from .. import models as models
from ..exceptions import NotEnoughProductLeft, TooBigToAdd
from .fixtures import factories

PRODUCT_TYPE_NUM = 5
ATTRIBUTE_NUM = 7
USER_NUM = CATEGORY_NUM = VENDOR_NUM = PRODUCT_SET_NUM = 10
BRAND_NUM = 14
PRODUCT_ITEM_NUM = 30


class UserCustomerFactoryMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = factories.UserFactory.create_batch(USER_NUM)
        cls.customers = factories.CustomerFactory.create_batch(USER_NUM)
        for user in cls.users:
            user.set_password(user.password)
            user.save(update_fields=("password",))


class VendorsBrandsFactoryMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendors = factories.VendorFactory.create_batch(VENDOR_NUM)
        cls.brands = factories.BrandFactory.create_batch(BRAND_NUM)


class AttributeProdTypeCategoryMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attributes = factories.ProductAttributeFactory.create_batch(
            ATTRIBUTE_NUM
        )
        cls.p_types = factories.ProductTypeFactory.create_batch(
            PRODUCT_TYPE_NUM, attribute_set=cls.attributes
        )
        cls.categories = factories.ProductCategoryFactory.create_batch(
            CATEGORY_NUM
        )


class DataFactoryMixin(
    UserCustomerFactoryMixin,
    VendorsBrandsFactoryMixin,
    AttributeProdTypeCategoryMixin,
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_sets = factories.ProductSetFactory.create_batch(
            PRODUCT_SET_NUM, categories=cls.categories
        )
        cls.product_items = factories.ProductItemFactory.create_batch(
            PRODUCT_ITEM_NUM, favorited_by=cls.customers
        )
        cls.stockpile = factories.StockFactory.create_batch(PRODUCT_ITEM_NUM)


class UserModelTestCase(UserCustomerFactoryMixin, TestCase):
    def setUp(self):
        self.customer = self.customers[0]

    def test_user_retrieved_along_with_customer_in_get_query(self):
        target_queries_num = 1
        with CaptureQueriesContext(connection) as ctx:
            models.Customer.objects.first()
            self.assertEquals(len(ctx.captured_queries), target_queries_num)

    def test_user_email_changes_when_changing_customer_email(self):
        new_email = "customer@hello.py"
        self.customer.email = new_email
        self.customer.refresh_from_db()
        self.assertEquals(self.customer.email, new_email)
        self.assertEquals(self.customer.email, self.customer.user.email)

    def test_user_first_name_changes_when_changing_customer_first_name_(self):
        new_first_name = "Tommy"
        self.customer.first_name = new_first_name
        self.customer.refresh_from_db()
        self.assertEquals(self.customer.first_name, new_first_name)
        self.assertEquals(
            self.customer.first_name, self.customer.user.first_name
        )

    def test_user_last_name_changes_when_changing_customer_last_name_(self):
        new_last_name = "Vercetti"
        self.customer.last_name = new_last_name
        self.customer.refresh_from_db()
        self.assertEquals(self.customer.last_name, new_last_name)
        self.assertEquals(
            self.customer.last_name, self.customer.user.last_name
        )

    def test_customer_username_change_fails(self):
        new_username = "tommyV"
        with self.assertRaises(AttributeError):
            self.customer.username = new_username

    def test_empty_cart_created_with_customer_creation(self):
        self.assertTrue(self.customer.cart)
        self.assertEquals(
            self.customer.cart.status, models.Cart.CartStatus.EMPTY
        )


class VendorBrandModelsTestCase(VendorsBrandsFactoryMixin, TestCase):
    def test_vendor_model_fields(self):
        for v in self.vendors:
            self.assertTrue(v.description)
            self.assertTrue(v.name)
            self.assertTrue(v.slug)

    def test_create_vendor_with_same_name_raises_error(self):
        vendor = self.vendors[0]
        with self.assertRaises(IntegrityError):
            models.Vendor.objects.create(name=vendor.name)

    def test_brand_model_fields(self):
        for b in self.brands:
            self.assertTrue(b.name)
            self.assertTrue(b.description)
            self.assertTrue(b.slug)
            self.assertTrue(b.vendor)

    def test_create_brand_with_same_name_raises_error(self):
        brand = self.brands[0]
        with self.assertRaises(IntegrityError):
            models.Brand.objects.create(name=brand.name)


class AttributeProductTypeCategoryTestCase(
    AttributeProdTypeCategoryMixin, TestCase
):
    def setUp(self):
        self.p_type = self.p_types[0]
        self.category = self.categories[0]

    def test_prod_type_has_auto_generated_slug_field(self):
        self.assertTrue(self.p_type.slug)

    def test_adding_duplicate_attribute_to_prod_type_raises_error(self):
        attr = self.p_type.attribute_set.first()
        with self.assertRaises(IntegrityError):
            models.ProductTypeToAttributeLinkTable.objects.create(
                product_type=self.p_type, attr=attr
            )

    def test_adding_new_attribute_to_prod_type_creates_new_constraint(self):
        attr_set = models.ProductTypeToAttributeLinkTable.objects.filter(
            product_type=self.p_type
        )
        self.assertEqual(
            len(self.p_type.attribute_set.all()), attr_set.count()
        )
        attr = models.ProductAttribute.objects.create(name="fake attribute")
        self.p_type.attribute_set.add(attr)
        self.assertEqual(
            len(self.p_type.attribute_set.all()), attr_set.count()
        )

    def test_create_prod_type_with_same_name_raises_error(self):
        with self.assertRaises(IntegrityError):
            models.ProductType.objects.create(
                name=self.p_type.name, logo="fake_img.jpg"
            )

    def test_create_attribute_with_same_name_raises_error(self):
        with self.assertRaises(IntegrityError):
            models.ProductAttribute.objects.create(
                name=self.attributes[0].name
            )

    def test_category_has_auto_generated_slug_field(self):
        self.assertTrue(self.category.slug)

    def test_category_verbose_names(self):
        self.assertEqual(
            self.category._meta.verbose_name,
            models.ProductCategory._meta.verbose_name,
        )
        self.assertEqual(
            self.category._meta.verbose_name_plural,
            models.ProductCategory._meta.verbose_name_plural,
        )

    def test_create_category_with_same_name_raises_error(self):
        with self.assertRaises(IntegrityError):
            models.ProductCategory.objects.create(name=self.category.name)


class ProdSetProdItemStockModelsTestCase(DataFactoryMixin, TestCase):
    def setUp(self):
        self.VALID_STOCK_AMOUNT = 20
        self.p_set = self.product_sets[0]
        self.p_item = self.product_items[0]
        self.stock = self.stockpile[0]

    def test_prod_set_has_auto_generated_slug_field(self):
        self.assertTrue(self.p_set.slug)

    def test_prod_item_has_custom_manager(self):
        self.assertIsInstance(
            self.p_item._meta.model.objects, models.ProductItemManager
        )

    def test_prod_item_has_auto_generated_sku_field(self):
        self.assertTrue(self.p_item.sku)
        self.assertEqual(self.p_item.sku, self.p_item._generate_sku())

    def test_prod_item_setting_views_raises_error(self):
        with self.assertRaises(AttributeError):
            self.p_item.views = 20

    def test_prod_item_increment_view_count_success(self):
        views = self.p_item.views
        self.p_item.increment_view_count()
        self.p_item.refresh_from_db()
        self.assertEqual(self.p_item.views, views + 1)

    def test_prod_item_discounted_price_returns_correct_result(self):
        disc_price_generated = self.p_item.discounted_price
        reg_price = self.p_item.regular_price
        disc = self.p_item.discount
        disc_price_counted = float(reg_price) - (
            float(reg_price) * (disc / 100)
        )
        self.assertIsInstance(disc_price_generated, Decimal)
        self.assertEqual(
            disc_price_generated.to_eng_string(),
            format(disc_price_counted, ".2f"),
        )

    def test_prod_item_creating_item_with_negative_discount_fails(self):
        with self.assertRaises(IntegrityError):
            factories.ProductItemFactory.create(
                pk=PRODUCT_ITEM_NUM + 1, discount=-1
            )

    def test_prod_item_creating_item_with_too_big_discount_fails(self):
        with self.assertRaises(IntegrityError):
            factories.ProductItemFactory.create(
                pk=PRODUCT_ITEM_NUM + 1, discount=100
            )

    # test to_dict method if it's not deprecated

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
            self.stock.set(models.MAX_AMOUNT_ADDED + 1)

    def test_stock_add_too_big_value_fails(self):
        """Raises specific error when trying to add more than allowed"""
        with self.assertRaises(TooBigToAdd):
            self.stock.add(models.MAX_AMOUNT_ADDED + 1)

    def test_stock_deduct_more_than_available_fails(self):
        """Raises specific error when trying to deduct more than current amount"""
        with self.assertRaises(NotEnoughProductLeft):
            self.stock.deduct(self.stock.amount + 1)

    def test_stock_methods_with_negative_numbers_fails(self):
        with self.assertRaises(ValidationError):
            self.stock.deduct(-1)
            self.stock.add(-1)
            self.stock.set(-1)


class CartOrderModelsTestCase(DataFactoryMixin, TestCase):
    def setUp(self):
        self.customer = self.customers[0]
        self.cart = models.Cart.objects.create(customer=self.customer)

    def test_empty_cart_attributes(self):
        self.assertEqual(self.cart.status, models.Cart.CartStatus.EMPTY)
        self.assertTrue(self.cart.empty)

    def test_add_inactive_prod_item_to_cart_fails(self):
        if p_item := models.ProductItem.objects.filter(
            is_active=False
        ).first():
            with self.assertRaises(ValidationError):
                models.CartItem.create_from_product_item(
                    self.customer.id, p_item.id
                )

    def test_add_prod_item_quantity_more_than_stock_available_fails(self):
        if p_item := models.ProductItem.objects.filter(is_active=True).first():
            available = p_item.stock.amount
            with self.assertRaises(ValidationError):
                models.CartItem.create_from_product_item(
                    self.customer.id, p_item.id, quantity=available + 1
                )

    def test_add_prod_item_valid_quantity_success(self):
        if p_item := models.ProductItem.objects.filter(is_active=True).first():
            available = p_item.stock.amount
            cart_item = models.CartItem.create_from_product_item(
                self.customer.id,
                p_item.id,
                quantity=random.randint(1, available),
            )
            self.assertFalse(self.cart.empty)
            self.assertEqual(self.cart.items.count(), 1)
            self.assertNotEqual(self.cart.created_at, self.cart.updated_at)
            self.assertLessEqual(cart_item.quantity, p_item.stock.amount)
            self.assertEqual(cart_item.sku, p_item.sku)
            self.assertEqual(cart_item.product_name, p_item.product_name)
            self.assertEqual(
                cart_item.discounted_price, p_item.discounted_price
            )

    def test_cart_item_adding_the_same_product_item_increases_quantity(self):
        FIRST_ADDED_QUANTITY = 2
        NEXT_ADDED_QUANTITY = 5
        if p_item := models.ProductItem.objects.filter(is_active=True).first():
            p_item.stock.add(10)
            cart_item = models.CartItem.create_from_product_item(
                self.customer.id,
                p_item.id,
                quantity=FIRST_ADDED_QUANTITY,
            )
            self.assertEqual(self.cart.items.count(), 1)
            self.assertEqual(cart_item.quantity, FIRST_ADDED_QUANTITY)
            cart_item2 = models.CartItem.create_from_product_item(
                self.customer.id,
                p_item.id,
                quantity=NEXT_ADDED_QUANTITY,
            )
            self.assertEqual(self.cart.items.count(), 1)
            self.assertEqual(
                cart_item2.quantity, FIRST_ADDED_QUANTITY + NEXT_ADDED_QUANTITY
            )
            self.assertEqual(cart_item.id, cart_item2.id)

    def test_cart_get_initial_sum_returns_expected_result(self):
        if p_item := models.ProductItem.objects.filter(is_active=True).first():
            available = p_item.stock.amount
            models.CartItem.create_from_product_item(
                self.customer.id,
                p_item.id,
                quantity=random.randint(1, available),
            )
            expected = sum(
                item.regular_price * item.quantity
                for item in self.cart.items.all()
            )
            self.assertEqual(self.cart.get_initial_sum(), expected)

    def test_cart_get_discounted_sum_returns_expected_result(self):
        if p_item := models.ProductItem.objects.filter(is_active=True).first():
            available = p_item.stock.amount
            models.CartItem.create_from_product_item(
                self.customer.id,
                p_item.id,
                quantity=random.randint(1, available),
            )
            expected = sum(
                item.discounted_price * item.quantity
                for item in self.cart.items.all()
            )
            self.assertEqual(self.cart.get_discounted_sum(), expected)

    def test_cart_get_total_discount_returns_expected_result(self):
        if p_item := models.ProductItem.objects.filter(is_active=True).first():
            available = p_item.stock.amount
            models.CartItem.create_from_product_item(
                self.customer.id,
                p_item.id,
                quantity=random.randint(1, available),
            )
            expected = sum(
                (item.regular_price - item.discounted_price) * item.quantity
                for item in self.cart.items.all()
            )
            self.assertEqual(self.cart.get_total_discount(), expected)

    def test_cart_item_unmark_for_order_prevents_from_being_counted(self):
        if p_item := models.ProductItem.objects.filter(is_active=True).first():
            available = p_item.stock.amount
            cart_item = models.CartItem.create_from_product_item(
                self.customer.id,
                p_item.id,
                quantity=random.randint(1, available),
            )
            self.assertGreater(self.cart.get_initial_sum(), 0)
            self.assertTrue(self.cart.items_ready_for_order.exists())
            cart_item.unmark_for_order()
            self.assertEqual(self.cart.get_initial_sum(), 0)
            self.assertFalse(self.cart.items_ready_for_order.exists())

    def test_cart_clear_out_deletes_all_items_and_sets_empty_status(self):
        if p_item := models.ProductItem.objects.filter(is_active=True).first():
            available = p_item.stock.amount
            models.CartItem.create_from_product_item(
                self.customer.id,
                p_item.id,
                quantity=random.randint(1, available),
            )
            self.assertFalse(self.cart.empty)
            self.cart.clear_out()
            self.assertTrue(self.cart.empty)
            self.assertEqual(self.cart.status, models.Cart.CartStatus.EMPTY)

    def test_order_creation_without_cart_raiess_error(self):
        self.cart.delete()
        with self.assertRaises(models.Cart.DoesNotExist):
            models.Order.create_from_cart(self.customer.id)

    def test_order_creation_with_empty_cart_raises_error(self):
        self.assertTrue(self.cart.empty)
        with self.assertRaises(models.Cart.DoesNotExist):
            models.Order.create_from_cart(self.customer.id)

    def test_order_creation_with_marked_cart_item_success(self):
        if p_item := models.ProductItem.objects.filter(is_active=True).first():
            available = p_item.stock.amount
            models.CartItem.create_from_product_item(
                self.customer.id,
                p_item.id,
                quantity=random.randint(1, available),
            )
            self.assertFalse(self.cart.empty)
            disc_sum = self.cart.get_discounted_sum()
            active_items = self.cart.items_ready_for_order.count()
            order = models.Order.create_from_cart(self.customer.id)
            self.assertTrue(order)
            self.assertEqual(order.discounted_sum, disc_sum)
            self.assertEqual(order.items.count(), active_items)

    def test_marked_cart_item_gets_deleted_after_order_creation(self):
        if p_item := models.ProductItem.objects.filter(is_active=True).first():
            available = p_item.stock.amount
            cart_item = models.CartItem.create_from_product_item(
                self.customer.id,
                p_item.id,
                quantity=random.randint(1, available),
            )
            models.Order.create_from_cart(self.customer.id)
            self.assertTrue(self.cart.empty)
            self.assertTrue(self.cart.status, models.Cart.CartStatus.EMPTY)
            with self.assertRaises(models.CartItem.DoesNotExist):
                cart_item.refresh_from_db()

    def test_order_creation_with_unmarked_cart_item_raises_error(self):
        if p_item := models.ProductItem.objects.filter(is_active=True).first():
            available = p_item.stock.amount
            models.CartItem.create_from_product_item(
                self.customer.id,
                p_item.id,
                quantity=random.randint(1, available),
                marked_for_order=False,
            )
            self.assertFalse(self.cart.empty)
            with self.assertRaises(models.CartItem.DoesNotExist):
                models.Order.create_from_cart(self.customer.id)


# from dbexample.models import *
# c = Cart.objects.first()
# c2 = Cart.objects.last()
# from django.db import connection, reset_queries
