# COMP7640 Multi-Vendor Marketplace

This repository is the refactored course-project version of `ECommerce-Grocery-Store`.
It now focuses on the COMP7640 brief: a Python + Flask + MySQL multi-vendor marketplace.

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

Reference SQL files in the project root:

- [`../vibhorag101-stage1-schema.sql`](../vibhorag101-stage1-schema.sql)
- [`../vibhorag101-stage2-sample-data.sql`](../vibhorag101-stage2-sample-data.sql)

## Local Setup

1. Install MySQL Server locally.
2. Create a Python virtual environment.
3. Install the project dependencies.
4. Make sure `database.yaml` points to your local MySQL instance.
5. Run the schema SQL, then the sample-data SQL.
6. Start the Flask app.

Example commands on Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\requirements.txt
py .\run.py
```

## Running the SQL

If MySQL is installed locally, you can run:

```powershell
mysql -u root -p < ..\vibhorag101-stage1-schema.sql
mysql -u root -p comp7640_marketplace < ..\vibhorag101-stage2-sample-data.sql
```

Or use the VS Code MySQL extension and execute the same files there.

## Key Pages

- `/` : role entry page
- `/loginRegisterUser` : customer entry
- `/loginRegisterSeller` : vendor entry
- `/home/<user_id>` : marketplace browse page
- `/sell/<vendor_id>` : vendor inventory management
- `/myOrders/<user_id>` : customer order history

## Verification

Lightweight verification commands used during development:

```powershell
python -m py_compile market\__init__.py market\routes.py
python -m unittest tests.test_marketplace_routes -v
```

## Project Notes

- The app has been migrated away from the original grocery-store/admin narrative.
- The current implementation is intentionally centered on the COMP7640 marketplace requirements.
- Historical files such as `Dump.sql` and `Submit/` are kept only as reference material for now.
