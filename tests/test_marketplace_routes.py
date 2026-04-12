import sys
import types
import unittest
from unittest.mock import patch

import yaml

fake_mysql_module = types.ModuleType("flask_mysqldb")


class FakeMySQL:
    def __init__(self, app):
        self.connection = None


fake_mysql_module.MySQL = FakeMySQL
sys.modules.setdefault("flask_mysqldb", fake_mysql_module)
fake_pyparsing_module = types.ModuleType("pyparsing")
fake_pyparsing_module.nums = ""
sys.modules.setdefault("pyparsing", fake_pyparsing_module)
original_yaml_load = yaml.load
yaml.load = lambda stream, Loader=None: original_yaml_load(stream, Loader=yaml.SafeLoader)

from market import routes


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))
        return len(self.rows)

    def fetchall(self):
        return self.rows

    def fetchone(self):
        if not self.rows:
            return None
        return self.rows[0]

    def close(self):
        return None


class FakeConnection:
    def __init__(self, rows):
        self.cursor_instance = FakeCursor(rows)
        self.committed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True


class MarketplaceRouteTests(unittest.TestCase):
    def test_get_all_vendors_formats_vendor_listing_rows(self):
        fake_rows = [
            (1, "Fresh Valley Market", "New Territories", 4.60, 3),
            (2, "Harbour Organic Hub", "Hong Kong Island", None, 1),
        ]
        fake_connection = FakeConnection(fake_rows)

        with patch.object(routes.my_sql, "connection", fake_connection):
            vendors = routes.get_all_vendors()

        self.assertEqual(2, len(vendors))
        self.assertEqual("Fresh Valley Market", vendors[0]["BusinessName"])
        self.assertEqual("New Territories", vendors[0]["Location"])
        self.assertEqual(4.60, vendors[0]["AverageRating"])
        self.assertEqual(3, vendors[0]["ProductCount"])

    def test_get_marketplace_products_formats_vendor_tags_and_stock(self):
        fake_rows = [
            (1, "Organic Spinach", 18.00, 98, "Fresh Valley Market", "vegetable,organic,healthy", "Fresh organic spinach bundle")
        ]
        fake_connection = FakeConnection(fake_rows)

        with patch.object(routes.my_sql, "connection", fake_connection):
            products = routes.get_marketplace_products()

        self.assertEqual(1, len(products))
        self.assertEqual("Organic Spinach", products[0]["Name"])
        self.assertEqual("Fresh Valley Market", products[0]["Vendor"])
        self.assertEqual(["vegetable", "organic", "healthy"], products[0]["Tags"])
        self.assertEqual(98, products[0]["Stock"])
        self.assertIsNone(fake_connection.cursor_instance.executed[0][1])

    def test_get_marketplace_products_uses_search_term_for_name_or_tag(self):
        fake_rows = [
            (7, "Organic Avocado", 24.00, 48, "Harbour Organic Hub", "organic,fruit,healthy", "Imported organic avocado")
        ]
        fake_connection = FakeConnection(fake_rows)

        with patch.object(routes.my_sql, "connection", fake_connection):
            products = routes.get_marketplace_products("organic")

        executed_query, executed_params = fake_connection.cursor_instance.executed[0]
        self.assertIn("LOWER(p.product_name) LIKE %s", executed_query)
        self.assertIn("LOWER(pt.tag_value) LIKE %s", executed_query)
        self.assertEqual(("%organic%", "%organic%"), executed_params)
        self.assertEqual("Organic Avocado", products[0]["Name"])

    def test_get_marketplace_products_applies_vendor_filter_when_present(self):
        fake_rows = [
            (7, "Organic Avocado", 24.00, 48, "Harbour Organic Hub", "organic,fruit,healthy", "Imported organic avocado")
        ]
        fake_connection = FakeConnection(fake_rows)

        with patch.object(routes.my_sql, "connection", fake_connection):
            routes.get_marketplace_products(vendor_id=7)

        executed_query, executed_params = fake_connection.cursor_instance.executed[0]
        self.assertIn("p.vendor_id = %s", executed_query)
        self.assertEqual((7,), executed_params)

    def test_get_vendor_products_formats_stock_and_tags(self):
        fake_rows = [
            (1, "Organic Spinach", 18.00, 98, "vegetable,organic,healthy", "active")
        ]
        fake_connection = FakeConnection(fake_rows)

        with patch.object(routes.my_sql, "connection", fake_connection):
            products = routes.get_vendor_products(1)

        self.assertEqual(1, len(products))
        self.assertEqual("Organic Spinach", products[0]["Name"])
        self.assertEqual(98, products[0]["Stock"])
        self.assertEqual(["vegetable", "organic", "healthy"], products[0]["Tags"])

    def test_get_recommendations_returns_empty_without_history_tags(self):
        fake_connection = FakeConnection([])

        with patch.object(routes.my_sql, "connection", fake_connection):
            products = routes.get_recommendations(1)

        self.assertEqual([], products)

    def test_create_vendor_inserts_vendor_record(self):
        fake_connection = FakeConnection([])

        with patch.object(routes.my_sql, "connection", fake_connection):
            routes.create_vendor(
                first_name="Alice",
                last_name="Wong",
                email="alice@example.com",
                password="secret123",
                contact_number="852-60000001",
                geographical_presence="Kowloon",
            )

        executed_query, executed_params = fake_connection.cursor_instance.executed[0]
        self.assertIn(f"INSERT INTO {routes.MARKETPLACE_DB}.vendor", executed_query)
        self.assertEqual("Alice Wong", executed_params[0])
        self.assertEqual("Alice", executed_params[1])
        self.assertEqual("alice@example.com", executed_params[2])
        self.assertEqual("852-60000001", executed_params[3])
        self.assertEqual("Kowloon", executed_params[5])

    def test_find_vendor_login_looks_up_vendor_by_email(self):
        fake_rows = [(3, "Harbour Organic Hub", "Cindy Lee", "cindy@example.com", "852-60000003", "pw_hash")]
        fake_connection = FakeConnection(fake_rows)

        with patch.object(routes.my_sql, "connection", fake_connection):
            vendor = routes.find_vendor_login("cindy@example.com")

        executed_query, executed_params = fake_connection.cursor_instance.executed[0]
        self.assertIn(f"FROM {routes.MARKETPLACE_DB}.vendor", executed_query)
        self.assertEqual(("cindy@example.com",), executed_params)
        self.assertEqual(fake_rows[0], vendor)

    def test_group_cart_items_aggregates_quantity_and_subtotal(self):
        grouped = routes.group_cart_items([
            {"ProductID": 1, "Name": "Organic Spinach", "VendorID": 1, "Vendor": "Fresh Valley Market", "Price": 18.0},
            {"ProductID": 1, "Name": "Organic Spinach", "VendorID": 1, "Vendor": "Fresh Valley Market", "Price": 18.0},
            {"ProductID": 4, "Name": "Whole Wheat Bread", "VendorID": 2, "Vendor": "Urban Daily Grocer", "Price": 22.0},
        ])

        self.assertEqual(2, len(grouped))
        self.assertEqual(2, grouped[0]["Quantity"])
        self.assertEqual(36.0, grouped[0]["Subtotal"])
        self.assertEqual(1, grouped[0]["VendorID"])
        self.assertEqual(22.0, grouped[1]["Subtotal"])

    def test_calculate_vendor_transaction_amounts_splits_by_vendor(self):
        grouped_items = [
            {"VendorID": 1, "Subtotal": 36.0},
            {"VendorID": 2, "Subtotal": 22.0},
            {"VendorID": 1, "Subtotal": 15.5},
        ]

        transactions = routes.calculate_vendor_transaction_amounts(grouped_items)

        self.assertEqual({1: 51.5, 2: 22.0}, transactions)

    def test_can_modify_order_allows_only_before_shipped(self):
        self.assertTrue(routes.can_modify_order("placed"))
        self.assertTrue(routes.can_modify_order("processing"))
        self.assertFalse(routes.can_modify_order("shipped"))
        self.assertFalse(routes.can_modify_order("cancelled"))

    def test_compute_order_total_sums_item_subtotals(self):
        total = routes.compute_order_total([
            {"Subtotal": 36.0},
            {"Subtotal": 22.0},
            {"Subtotal": 15.5},
        ])

        self.assertEqual(73.5, total)

    def test_vendors_route_renders_vendor_template_with_vendors(self):
        fake_vendors = [
            {
                "VendorID": 1,
                "BusinessName": "Fresh Valley Market",
                "Location": "NT",
                "AverageRating": 4.6,
                "ProductCount": 3,
            }
        ]

        with patch.object(routes, "get_all_vendors", return_value=fake_vendors), \
             patch.object(routes, "get_browse_customer_id", return_value=None), \
             patch.object(routes, "render_template", return_value="rendered") as render_mock:
            result = routes.vendorListing()

        self.assertEqual("rendered", result)
        render_mock.assert_called_once_with("vendors.html", vendors=fake_vendors, browse_user_id=None)

    def test_homepage_shows_current_store_banner_without_clear_filter_button(self):
        with routes.app.test_request_context("/home/1?vendor_id=1"):
            routes.session["role"] = "customer"
            routes.session["user_id"] = 1

            with patch.object(routes, "get_marketplace_products", return_value=[]), \
                 patch.object(routes, "get_recommendations", return_value=[]), \
                 patch.object(routes, "find_vendor_login_by_id", return_value=(1, "Fresh Valley Market")):
                rendered = routes.homepage("1")

        self.assertIn("Current store:", rendered)
        self.assertIn("Fresh Valley Market", rendered)
        self.assertNotIn("Clear Vendor Filter", rendered)
        self.assertNotIn("Viewing products from", rendered)

    def test_login_register_user_page_uses_marketplace_image(self):
        with routes.app.test_request_context("/loginRegisterUser"):
            rendered = routes.loginRegisterUser()

        self.assertIn("Marketplace.png", rendered)
        self.assertNotIn("store.jpg", rendered)

    def test_login_register_seller_page_uses_marketplace_image(self):
        with routes.app.test_request_context("/loginRegisterSeller"):
            rendered = routes.loginRegisterSeller()

        self.assertIn("Marketplace.png", rendered)
        self.assertNotIn("store.jpg", rendered)

    def test_is_authenticated_does_not_allow_guest_role(self):
        with routes.app.test_request_context('/'):
            routes.session["role"] = "guest"
            self.assertFalse(routes.is_authenticated(1, "customer"))
            self.assertFalse(routes.is_authenticated(2, "vendor"))


if __name__ == "__main__":
    unittest.main()
