# E-commerce Functional Copy Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify English functional copy for customer and vendor workflows so buttons, statuses, titles, and messages use common platform-style e-commerce wording.

**Architecture:** Keep all behavior, routes, translation keys, and status codes unchanged. Update only displayed English text in the translation table plus any hardcoded functional UI strings in templates or frontend scripts, then verify by search and tests.

**Tech Stack:** Python, Flask, Jinja templates, JavaScript, pytest, ripgrep

---

### Task 1: Audit Workflow Copy Sources

**Files:**
- Modify: `docs/superpowers/plans/2026-04-13-ecommerce-copy-simplification.md`
- Inspect: `market/translations.py`
- Inspect: `market/templates/base.html`
- Inspect: `market/templates/home.html`
- Inspect: `market/templates/order.html`
- Inspect: `market/templates/orderDetails.html`
- Inspect: `market/templates/customerOrders.html`
- Inspect: `market/templates/vendorOrders.html`
- Inspect: `market/templates/addProduct.html`
- Inspect: `market/routes.py`

- [ ] **Step 1: Search for workflow-facing English copy**

```powershell
rg -n "Bag|Archive|Fulfillment|Vault|Collective|Discovery|Artisanal|Acquisition|Dispatched|Sign In|Checkout|Order|Cart|Shop|Vendor" market/translations.py market/templates market/routes.py
```

- [ ] **Step 2: Review the results and map them to three buckets**

```text
Bucket A: translation-backed functional copy to change in market/translations.py
Bucket B: hardcoded functional copy in templates or JS to change in place
Bucket C: branded or marketing copy to leave untouched
```

- [ ] **Step 3: Confirm the in-scope files before editing**

```text
Primary edit targets:
- market/translations.py
- market/templates/base.html
- Any workflow template with hardcoded functional labels discovered in Step 1
```

- [ ] **Step 4: Commit the audit checkpoint**

```bash
git add docs/superpowers/plans/2026-04-13-ecommerce-copy-simplification.md
git commit -m "docs: add copy simplification implementation plan"
```

### Task 2: Simplify Translation-Backed Functional Copy

**Files:**
- Modify: `market/translations.py`
- Test: `tests/test_marketplace_routes.py`

- [ ] **Step 1: Write the expected wording list before editing**

```text
Use these replacements where the keys are functional:
- My Bag -> My Cart
- Add to Bag -> Add to Cart
- Enter Studio -> Visit Shop
- Join to Browse -> Sign in to Browse
- Order Archive -> Orders
- Fulfillment Center -> Orders
- Fulfillment Console -> Manage Orders
- Mark as Shipped -> Ship Order
- Proceed to Checkout -> Checkout
- Place Order Now -> Place Order
- Discovery Formed -> Placed
- Artisan Handling -> Processing
- Dispatched -> Shipped
- Acquisition Secured -> Completed
- Access Denied. Please authenticate. -> Please sign in first.
- Unit added to your collection bag. -> Item added to cart.
```

- [ ] **Step 2: Update English values only in `market/translations.py`**

```python
# Keep this structure unchanged:
TRANSLATIONS = {
    'en': {
        'nav_orders': 'Orders',
        'nav_my_bag': 'My Cart',
        'add_to_bag': 'Add to Cart',
        'enter_studio': 'Visit Shop',
        'join_to_browse': 'Sign in to Browse',
        'fulfillment_title': 'Orders',
        'order_archive': 'Orders',
        'ship_btn': 'Ship Order',
        'checkout_btn': 'Checkout',
        'place_order_btn': 'Place Order',
        'status_placed': 'Placed',
        'status_processing': 'Processing',
        'status_shipped': 'Shipped',
        'status_cancelled': 'Cancelled',
        'flash_access_denied': 'Please sign in first.',
        'msg_added_to_cart': 'Item added to cart.',
    }
}
```

- [ ] **Step 3: Preserve runtime behavior**

```text
Do not change:
- translation keys
- `placed`, `processing`, `shipped`, `cancelled` status codes
- `get_text(...)` call sites
```

- [ ] **Step 4: Run focused tests after the translation update**

```powershell
pytest tests/test_marketplace_routes.py -q
```

Expected:

```text
All tests pass.
```

- [ ] **Step 5: Commit the translation update**

```bash
git add market/translations.py tests/test_marketplace_routes.py
git commit -m "refactor: simplify English ecommerce workflow copy"
```

### Task 3: Clean Hardcoded Functional Copy In Templates And Scripts

**Files:**
- Modify: `market/templates/base.html`
- Modify: `market/templates/home.html`
- Modify: `market/templates/order.html`
- Modify: `market/templates/orderDetails.html`
- Modify: `market/templates/customerOrders.html`
- Modify: `market/templates/vendorOrders.html`
- Modify: `market/templates/addProduct.html`
- Modify: `market/templates/UserLogin.html`
- Modify: `market/templates/SellerLogin.html`
- Modify: `market/routes.py` if any hardcoded workflow message remains

- [ ] **Step 1: Search for remaining hardcoded English strings after Task 2**

```powershell
rg -n "\"[^\"]*[A-Za-z][^\"]*\"|'[^']*[A-Za-z][^']*'" market/templates/base.html market/templates/home.html market/templates/order.html market/templates/orderDetails.html market/templates/customerOrders.html market/templates/vendorOrders.html market/templates/addProduct.html market/templates/UserLogin.html market/templates/SellerLogin.html market/routes.py
```

- [ ] **Step 2: Replace only functional wording in place**

```html
<!-- Example in base.html -->
feedback.textContent = 'Failed to add item. Please try again.';

<!-- Update to -->
feedback.textContent = 'Could not add item to cart. Please try again.';
```

```html
<!-- Leave placeholders like this alone because they are neutral and functional enough -->
<input placeholder="you@example.com">
```

- [ ] **Step 3: Keep branded and atmospheric text untouched**

```text
Do not rewrite hero headings, portal descriptions, or other marketing copy that was explicitly excluded from scope.
```

- [ ] **Step 4: Re-run the workflow test file**

```powershell
pytest tests/test_marketplace_routes.py -q
```

Expected:

```text
All tests pass.
```

- [ ] **Step 5: Commit the template/script cleanup**

```bash
git add market/templates/base.html market/templates/home.html market/templates/order.html market/templates/orderDetails.html market/templates/customerOrders.html market/templates/vendorOrders.html market/templates/addProduct.html market/templates/UserLogin.html market/templates/SellerLogin.html market/routes.py
git commit -m "refactor: align hardcoded workflow copy with ecommerce wording"
```

### Task 4: Verify No Ornate Workflow Terms Remain In Functional Copy

**Files:**
- Inspect: `market/translations.py`
- Inspect: `market/templates/`
- Inspect: `market/routes.py`

- [ ] **Step 1: Re-scan the repository for avoided terms**

```powershell
rg -n "Bag|Archive|Fulfillment|Vault|Collective|Discovery Formed|Artisan Handling|Dispatched|Acquisition Secured" market/translations.py market/templates market/routes.py
```

- [ ] **Step 2: Manually review remaining hits**

```text
Keep a hit only if it is clearly branding or marketing copy.
Change it if it is a button, badge, title, prompt, or system message.
```

- [ ] **Step 3: Run the test suite**

```powershell
pytest -q
```

Expected:

```text
All tests pass.
```

- [ ] **Step 4: Inspect git diff for scope control**

```powershell
git diff -- market/translations.py market/templates/base.html market/templates/home.html market/templates/order.html market/templates/orderDetails.html market/templates/customerOrders.html market/templates/vendorOrders.html market/templates/addProduct.html market/templates/UserLogin.html market/templates/SellerLogin.html market/routes.py
```

- [ ] **Step 5: Commit the verification checkpoint**

```bash
git add market/translations.py market/templates/base.html market/templates/home.html market/templates/order.html market/templates/orderDetails.html market/templates/customerOrders.html market/templates/vendorOrders.html market/templates/addProduct.html market/templates/UserLogin.html market/templates/SellerLogin.html market/routes.py tests/test_marketplace_routes.py
git commit -m "test: verify simplified ecommerce workflow wording"
```

### Task 5: Publish The Changes

**Files:**
- Inspect: `.git`

- [ ] **Step 1: Check branch status**

```powershell
git status --short
git branch --show-current
git remote -v
```

- [ ] **Step 2: Push the current branch**

```powershell
git push origin HEAD
```

Expected:

```text
Push completes successfully.
```

- [ ] **Step 3: Share the final verification summary**

```text
Include:
- files changed
- representative wording changes
- tests run
- push result
```
