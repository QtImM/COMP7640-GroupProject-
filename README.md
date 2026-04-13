# BU Marketplace - COMP7640 Project

BU Marketplace is a database-driven multi-vendor e-commerce platform for COMP7640.

## Current Scope

The project currently supports these core flows:

- customer registration and login
- vendor registration and login
- marketplace product browsing
- search by partial product name or tag
- vendor-side product management
- cart-to-order checkout flow
- order creation across multiple vendors
- customer order history
- order cancellation before shipment
- order-item removal before shipment

## 1-Minute Local Start (Windows PowerShell)

From repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS comp7640_marketplace CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p comp7640_marketplace < bu-marketplace-stage1-schema.sql
mysql -u root -p comp7640_marketplace < bu-marketplace-stage2-sample-data.sql

py run.py
```

Then open `http://127.0.0.1:5000/`.

## database.yaml Template

Create or update `database.yaml`:

```yaml
mysql_host: "127.0.0.1"
mysql_user: "root"
mysql_password: "YOUR_LOCAL_PASSWORD"
mysql_db: "comp7640_marketplace"
```

Do not commit real passwords.

## Acceptance Mapping (COMP7640)

| Requirement | Implementation | How to Verify |
| --- | --- | --- |
| Vendor listing and onboarding | routes `/vendors` and `/sellerRegister`; `vendor` table with business profile fields | Open `/vendors` to confirm all vendors are listed, then register a new vendor and verify it appears in the marketplace |
| Browse all products offered by each vendor | public route `/vendors`; logged-in customers can open `/home/<user_id>?vendor_id=<vendor_id>` | Open `/vendors`, then from a customer session click `View Products` and confirm the marketplace view is filtered to the selected vendor |
| Multi-vendor order with per-item quantity | `orders` + `order_item` + `vendor_transaction`; route `/placeOrder/<user_id>` | Place items from different vendors in one cart, then check `orders/order_item/vendor_transaction` records |
| Product stock quantity and safe deduction | `product.stock_quantity`; atomic update `SET stock_quantity = stock_quantity - ? WHERE stock_quantity >= ?` | Try placing order beyond stock and confirm checkout is blocked |
| Search by partial product name or tag | route `/home/<user_id>?q=<keyword>` and marketplace search SQL | Search by partial name and by tag, confirm product list changes |
| Modify/cancel before shipment | routes `/cancelOrder/<user_id>/<order_id>` and `/removeOrderItem/<user_id>/<order_id>/<order_item_id>`; `can_modify_order` rule | Create order, cancel or remove item before shipment, confirm status/rows update |
| Vendor-side inventory management | `vendor` + `product` + `product_tag`; route `/sell/<vendor_id>` | Vendor login, add/update product with stock and tags, verify in marketplace page |

## Database

The local MySQL database used by the app is:

- database: `comp7640_marketplace`

Core tables:

- `vendor`
- `customer`
- `product`
- `product_tag`
- `orders`
- `order_item`
- `vendor_transaction`

Supplemental runtime table:

- `cart_item` (used by cart-to-order flow)

Reference SQL files in repository root:

- `bu-marketplace-stage1-schema.sql`
- `bu-marketplace-stage2-sample-data.sql`

## Key Pages

- `/`: role entry page
- `/vendors`: public vendor directory
- `/loginRegisterUser`: customer entry
- `/loginRegisterSeller`: vendor entry
- `/home/<user_id>`: marketplace browse page
- `/sell/<vendor_id>`: vendor inventory management
- `/myOrders/<user_id>`: customer order history

## Verification

```powershell
python -m py_compile market\__init__.py market\routes.py
python -m unittest discover -s tests -p "test_*.py" -v
```

## Project Notes

- The app has been migrated away from the original grocery-store/admin narrative.
- The implementation is centered on COMP7640 marketplace requirements.
- Historical files such as `Dump.sql` and `Submit/` are kept only as references.
