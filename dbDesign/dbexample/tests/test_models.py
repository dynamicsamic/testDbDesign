import random
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, reset_queries
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from .. import models as models
from ..exceptions import NotEnoughProductLeft, TooBigToAdd
from .fixtures import factories

PRODUCT_TYPE_NUM = DISCOUNT_NUM = 5
ATTRIBUTE_NUM = 7
USER_NUM = CATEGORY_NUM = VENDOR_NUM = PRODUCT_NUM = 10
BRAND_NUM = 14
PRODUCT_VERSION_NUM = 30


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
            PRODUCT_TYPE_NUM, attributes=cls.attributes
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
        cls.products = factories.ProductFactory.create_batch(
            PRODUCT_NUM, categories=cls.categories
        )
        cls.discounts = factories.ProductDiscountFactory.create_batch(
            DISCOUNT_NUM
        )
        cls.product_verions = factories.ProductVersionFactory.create_batch(
            PRODUCT_VERSION_NUM, favorited_by=cls.customers
        )
        cls.stockpile = factories.StockFactory.create_batch(
            PRODUCT_VERSION_NUM
        )


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

    def test_customer_username_change_raises_error(self):
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
        attr = self.p_type.attributes.first()
        with self.assertRaises(IntegrityError):
            models.ProductTypeToAttributeLinkTable.objects.create(
                product_type=self.p_type, attr=attr
            )

    def test_adding_new_attribute_to_prod_type_creates_new_constraint(self):
        attr_set = models.ProductTypeToAttributeLinkTable.objects.filter(
            product_type=self.p_type
        )
        self.assertEqual(len(self.p_type.attributes.all()), attr_set.count())
        attr = models.ProductAttribute.objects.create(name="fake attribute")
        self.p_type.attributes.add(attr)
        self.assertEqual(len(self.p_type.attributes.all()), attr_set.count())

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


class ProductProdVersionProdDiscountStockModelsTestCase(
    DataFactoryMixin, TestCase
):
    def setUp(self):
        self.VALID_STOCK_AMOUNT = 20
        self.product = self.products[0]
        # self.prod_version = self.product_verions[0]
        self.prod_version = models.ProductVersion.objects.filter(
            discount__is_active=True
        ).first()
        self.assertTrue(self.prod_version)
        self.stock = self.stockpile[0]

    def test_product_has_auto_generated_slug_field(self):
        self.assertTrue(self.product.slug)

    def test_product_has_prod_type_foreign_key(self):
        self.assertIsInstance(self.product.p_type, models.ProductType)

    def test_product_has_brand_foreign_key(self):
        self.assertIsInstance(self.product.brand, models.Brand)

    def test_product_has_category_many_to_many(self):
        categories = self.product.categories.all()
        self.assertTrue(categories)
        self.assertTrue(
            all(
                isinstance(category, models.ProductCategory)
                for category in categories
            )
        )

    def test_product_can_set_discount_to_its_versions(self):
        versions = self.product.versions
        if versions.exists():

            # initially set all versions discount to None
            versions.update(discount=None)
            self.assertTrue(
                all(version.discount is None for version in versions.all())
            )

            from django.utils import timezone

            now = timezone.now()
            if discount := models.ProductDiscount.objects.filter(
                is_active=True, starts_at__lte=now, ends_at__gt=now
            ).first():
                versions_len = versions.count()
                updated = self.product.set_discount_for_versions(discount.id)
                self.assertEqual(updated, versions_len)
                self.assertTrue(
                    all(
                        version.discount_id == discount.id
                        for version in versions.all()
                    )
                )

    def test_product_discount_create_with_negative_discount_raises_error(
        self,
    ):
        discount_data = {
            "pk": DISCOUNT_NUM + 1,
            "label": "test_discount",
            "rate": -20,
            "starts_at": "2022-11-15 20:35:19.799050+00:00",
            "ends_at": "2022-12-02 20:35:19.799050+00:00",
        }
        with self.assertRaises(IntegrityError):
            factories.ProductDiscountFactory.create(**discount_data)

    def test_product_discount_create_with_too_big_discount_raises_error(
        self,
    ):
        discount_data = {
            "pk": DISCOUNT_NUM + 1,
            "label": "test_discount",
            "rate": 120,
            "starts_at": "2022-11-15 20:35:19.799050+00:00",
            "ends_at": "2022-12-02 20:35:19.799050+00:00",
        }
        with self.assertRaises(IntegrityError):
            factories.ProductDiscountFactory.create(**discount_data)

    def test_product_version_has_custom_manager(self):
        self.assertIsInstance(
            self.prod_version._meta.model.objects, models.ProductVersionManager
        )

    def test_product_version_has_auto_generated_sku_field(self):
        self.assertTrue(self.prod_version.sku)
        self.assertEqual(
            self.prod_version.sku, self.prod_version._generate_sku()
        )

    def test_product_version_name_created_from_general_product(self):
        self.assertTrue(self.prod_version.name.startswith(self.product.name))

    def test_product_version_setting_views_raises_error(self):
        with self.assertRaises(AttributeError):
            self.prod_version.views = 20

    def test_product_version_increment_view_count_success(self):
        views = self.prod_version.views
        self.prod_version.increment_view_count()
        self.prod_version.refresh_from_db()
        self.assertEqual(self.prod_version.views, views + 1)

    def test_product_versions_have_discount_foreign_key_or_none(self):
        self.assertTrue(
            all(
                isinstance(p.discount, (models.ProductDiscount, type(None)))
                for p in self.product_verions
            )
        )

    def test_product_version_has_discount_rate_property(self):
        self.assertEqual(
            self.prod_version.discount_rate, self.prod_version.discount.rate
        )
        self.assertGreaterEqual(self.prod_version.discount_rate, 0)
        self.prod_version.discount = None
        self.prod_version.save()
        self.assertEqual(self.prod_version.discount_rate, 0)

    def test_product_version_discounted_price_returns_correct_result(self):
        disc_price_generated = self.prod_version.discounted_price
        reg_price = self.prod_version.regular_price
        disc = self.prod_version.discount.rate
        disc_price_counted = float(reg_price) - (
            float(reg_price) * (disc / 100)
        )
        self.assertIsInstance(disc_price_generated, Decimal)
        self.assertEqual(
            disc_price_generated.to_eng_string(),
            format(disc_price_counted, ".2f"),
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

    def test_stock_set_too_big_value_raises_error(self):
        """Raises specific error when trying to set more than allowed"""
        with self.assertRaises(ValidationError):
            self.stock.set(models.MAX_AMOUNT_ADDED + 1)

    def test_stock_add_too_big_value_raises_error(self):
        """Raises specific error when trying to add more than allowed"""
        with self.assertRaises(TooBigToAdd):
            self.stock.add(models.MAX_AMOUNT_ADDED + 1)

    def test_stock_deduct_more_than_available_raises_error(self):
        """Raises specific error when trying to deduct more than current amount"""
        with self.assertRaises(NotEnoughProductLeft):
            self.stock.deduct(self.stock.amount + 1)

    def test_stock_methods_with_negative_numbers_raises_error(self):
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
        self.assertTrue(self.cart.is_empty)

    def test_add_inactive_product_version_to_cart_raises_error(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=False
        ).first():
            with self.assertRaises(ValidationError):
                models.CartItem.objects.create_from_product_version(
                    self.customer.id, prod_version.id
                )

    def test_add_product_version_quantity_more_than_stock_available_raises_error(
        self,
    ):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            available = prod_version.stock.amount
            with self.assertRaises(ValidationError):
                models.CartItem.objects.create_from_product_version(
                    self.customer.id, prod_version.id, quantity=available + 1
                )

    def test_add_product_version_valid_quantity_success(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            available = prod_version.stock.amount
            cart_item = models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=random.randint(1, available),
            )
            self.assertFalse(self.cart.is_empty)
            self.assertEqual(self.cart.items.count(), 1)
            self.assertNotEqual(self.cart.created_at, self.cart.updated_at)
            self.assertLessEqual(cart_item.quantity, prod_version.stock.amount)
            self.assertEqual(cart_item.sku, prod_version.sku)
            self.assertEqual(cart_item.product_name, prod_version.product_name)
            self.assertEqual(
                cart_item.discounted_price, prod_version.discounted_price
            )

    def test_cart_item_adding_the_same_product_version_increases_quantity(
        self,
    ):
        FIRST_ADDED_QUANTITY = 2
        NEXT_ADDED_QUANTITY = 5
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            prod_version.stock.add(10)
            cart_item = models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=FIRST_ADDED_QUANTITY,
            )
            self.assertEqual(self.cart.items.count(), 1)
            self.assertEqual(cart_item.quantity, FIRST_ADDED_QUANTITY)
            cart_item2 = models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=NEXT_ADDED_QUANTITY,
            )
            self.assertEqual(self.cart.items.count(), 1)
            self.assertEqual(
                cart_item2.quantity, FIRST_ADDED_QUANTITY + NEXT_ADDED_QUANTITY
            )
            self.assertEqual(cart_item.id, cart_item2.id)

    def test_cart_get_initial_sum_returns_expected_result(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            available = prod_version.stock.amount
            models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=random.randint(1, available),
            )
            expected = sum(
                item.regular_price * item.quantity
                for item in self.cart.items.all()
            )
            self.assertEqual(self.cart.get_initial_sum(), expected)

    def test_cart_get_discounted_sum_returns_expected_result(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            available = prod_version.stock.amount
            models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=random.randint(1, available),
            )
            expected = sum(
                item.discounted_price * item.quantity
                for item in self.cart.items.all()
            )
            self.assertEqual(self.cart.get_discounted_sum(), expected)

    def test_cart_get_total_discount_returns_expected_result(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            available = prod_version.stock.amount
            models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=random.randint(1, available),
            )
            expected = sum(
                (item.regular_price - item.discounted_price) * item.quantity
                for item in self.cart.items.all()
            )
            self.assertEqual(self.cart.get_total_discount(), expected)

    def test_cart_item_unmark_for_order_prevents_from_being_counted(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            available = prod_version.stock.amount
            cart_item = models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=random.randint(1, available),
            )
            self.assertGreater(self.cart.get_initial_sum(), 0)
            self.assertTrue(self.cart.items_ready_for_order.exists())
            cart_item.unmark_for_order()
            self.assertEqual(self.cart.get_initial_sum(), 0)
            self.assertFalse(self.cart.items_ready_for_order.exists())

    def test_cart_clear_method_deletes_all_items_and_sets_empty_status(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            available = prod_version.stock.amount
            models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=random.randint(1, available),
            )
            self.assertFalse(self.cart.is_empty)
            self.cart.clear()
            self.assertTrue(self.cart.is_empty)
            self.assertEqual(self.cart.status, models.Cart.CartStatus.EMPTY)

    def test_order_creation_without_cart_raiess_error(self):
        self.cart.delete()
        with self.assertRaises(models.Cart.DoesNotExist):
            models.Order.objects.create_from_cart(self.customer.id)

    def test_order_creation_with_empty_cart_raises_error(self):
        self.assertTrue(self.cart.is_empty)
        with self.assertRaises(models.Cart.DoesNotExist):
            models.Order.objects.create_from_cart(self.customer.id)

    def test_order_creation_with_marked_cart_item_success(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            available = prod_version.stock.amount
            models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=random.randint(1, available),
            )
            self.assertFalse(self.cart.is_empty)
            disc_sum = self.cart.get_discounted_sum()
            active_items = self.cart.items_ready_for_order.count()
            order = models.Order.objects.create_from_cart(self.customer.id)
            self.assertTrue(order)
            self.assertEqual(order.discounted_sum, disc_sum)
            self.assertEqual(order.items.count(), active_items)

    def test_marked_cart_item_gets_deleted_after_order_creation(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            available = prod_version.stock.amount
            cart_item = models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=random.randint(1, available),
            )
            models.Order.objects.create_from_cart(self.customer.id)
            self.assertTrue(self.cart.is_empty)
            self.assertTrue(self.cart.status, models.Cart.CartStatus.EMPTY)
            with self.assertRaises(models.CartItem.DoesNotExist):
                cart_item.refresh_from_db()

    def test_order_creation_with_unmarked_cart_item_raises_error(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            available = prod_version.stock.amount
            models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=random.randint(1, available),
                marked_for_order=False,
            )
            self.assertFalse(self.cart.is_empty)
            with self.assertRaises(models.CartItem.DoesNotExist):
                models.Order.objects.create_from_cart(self.customer.id)

    def test_order_creation_affects_stock_attributes(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            stock = prod_version.stock
            initial_amount = stock.amount
            items_sold = stock.items_sold
            quantity = random.randint(1, initial_amount)
            models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=quantity,
            )
            order = models.Order.objects.create_from_cart(self.customer.id)
            stock.refresh_from_db()
            self.assertTrue(order)
            self.assertEqual(stock.amount, initial_amount - quantity)
            self.assertEqual(stock.items_sold, items_sold + quantity)

    def test_order_canceled_by_customer_success(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            stock = prod_version.stock
            initial_amount = stock.amount
            items_sold = stock.items_sold
            quantity = random.randint(1, initial_amount)
            models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=quantity,
            )
            order = models.Order.objects.create_from_cart(self.customer.id)
            order.cancel("customer")
            self.assertEqual(
                order.status, models.Order.OrderStatus.CANCELED_BY_CUSTOMER
            )
            self.assertTrue(
                all(item.is_canceled for item in order.items.all())
            )
            stock.refresh_from_db()
            self.assertEqual(stock.amount, initial_amount)
            self.assertEqual(stock.items_sold, items_sold)

    def test_order_canceled_by_seller_success(self):
        if prod_version := models.ProductVersion.objects.filter(
            is_active=True
        ).first():
            stock = prod_version.stock
            initial_amount = stock.amount
            items_sold = stock.items_sold
            quantity = random.randint(1, initial_amount)
            models.CartItem.objects.create_from_product_version(
                self.customer.id,
                prod_version.id,
                quantity=quantity,
            )
            order = models.Order.objects.create_from_cart(self.customer.id)
            order.cancel("seller")
            self.assertEqual(
                order.status, models.Order.OrderStatus.CANCELED_BY_SELLER
            )
            self.assertTrue(
                all(item.is_canceled for item in order.items.all())
            )
            stock.refresh_from_db()
            self.assertEqual(stock.amount, initial_amount)
            self.assertEqual(stock.items_sold, items_sold)


# from dbexample.models import *
# c = Cart.objects.first()
# c2 = Cart.objects.last()
# from django.db import connection, reset_queries
