# E-commerce Functional Copy Simplification Design

## Goal

Simplify English functional copy across the marketplace so buttons, statuses, and system messages use common platform-style e-commerce language. Keep brand and marketing language such as `Marketplace` intact.

## Scope

In scope:
- English button labels
- English order and product statuses
- English flash messages and AJAX feedback
- English functional page titles when they describe workflow pages
- Hardcoded functional UI text in templates and frontend scripts

Out of scope:
- Brand names
- Marketing or atmospheric copy
- Chinese translations unless needed to preserve existing behavior
- Route names, translation keys, backend identifiers, and database values

## Vocabulary Standard

Use this terminology consistently:
- `Cart` for customer shopping container
- `Vendor` for platform-side seller references
- `Shop` for customer-facing entry into a vendor storefront
- `Orders` for customer and vendor order history / management pages

Preferred style:
- Short action-first buttons: `Add to Cart`, `Checkout`, `Place Order`, `Save Changes`
- Familiar order statuses: `Placed`, `Processing`, `Shipped`, `Cancelled`
- Direct system messages: `Item added to cart.`, `Out of stock.`, `Please sign in first.`

Avoid in functional copy:
- `Bag`
- `Archive`
- `Fulfillment`
- `Vault`
- `Collective`
- `Discovery`
- `Artisanal`
- `Acquisition`
- `Dispatched`

## Approach Options Considered

### Option 1: Update translations only

Pros:
- Lowest implementation risk
- Fastest change set

Cons:
- Misses hardcoded text in templates and JavaScript
- Leaves inconsistent UX in some flows

### Option 2: Update translations plus hardcoded functional copy

Pros:
- Covers the full user-facing workflow
- Produces consistent wording across backend flash messages, templates, and AJAX feedback
- Keeps implementation risk low because only displayed text changes

Cons:
- Requires a broader pass across templates and scripts

Recommendation:
- Choose this option

### Option 3: Rewrite all English copy including marketing language

Pros:
- Most comprehensive tone reset

Cons:
- Exceeds requested scope
- Higher review cost and more subjective changes

## Planned Changes

### Translation Table

Update English values in `market/translations.py` for functional keys only. Keep existing keys unchanged so templates and routes continue working without code changes.

Examples:
- `My Bag` -> `My Cart`
- `Add to Bag` -> `Add to Cart`
- `Enter Studio` -> `Visit Shop`
- `Order Archive` -> `Orders`
- `Fulfillment Center` / `Fulfillment Console` -> `Orders` / `Manage Orders`
- `Discovery Formed` -> `Placed`
- `Artisan Handling` -> `Processing`
- `Dispatched` -> `Shipped`
- `Proceed to Checkout` -> `Checkout`
- `Place Order Now` -> `Place Order`

### Hardcoded Functional Text

Review templates and JS for direct English strings not sourced from translations, especially:
- form placeholders and link labels
- async add-to-cart failure messages
- fallback labels around orders and inventory workflows

Replace only functional wording. Leave descriptive or branded copy untouched.

### Consistency Rules

Apply the same wording across:
- navigation
- page titles for transactional pages
- table headers
- badges
- buttons
- flash messages
- AJAX responses

Do not rename:
- translation keys
- route paths
- status values stored in code or database logic (`placed`, `processing`, `shipped`, `cancelled`)

## Files Expected To Change

- `market/translations.py`
- `market/templates/base.html`
- customer and vendor workflow templates under `market/templates/`
- possibly `market/routes.py` only if a functional message is hardcoded there

## Verification Plan

1. Search the project for functional English copy and update the remaining hardcoded strings.
2. Re-scan for avoided terms in workflow-facing text.
3. Run the relevant test suite.
4. Review the main user flows manually in code:
   - marketplace browse
   - product detail
   - cart
   - checkout
   - customer orders
   - vendor orders

## Risks And Mitigations

Risk:
- Accidentally changing brand or marketing tone outside the requested scope

Mitigation:
- Restrict edits to buttons, statuses, prompts, system messages, and transactional titles only

Risk:
- Inconsistent wording between translation-backed text and hardcoded text

Mitigation:
- Perform a final repository-wide search for old workflow terms after edits

Risk:
- Breaking behavior by changing identifiers instead of display strings

Mitigation:
- Keep keys, route names, and status codes unchanged

## Acceptance Criteria

- Functional English copy uses common platform e-commerce wording
- `Cart`, `Vendor`, `Shop`, and `Orders` are used consistently according to the agreed standard
- Order statuses read as `Placed`, `Processing`, `Shipped`, and `Cancelled`
- No functional UI text still uses obviously ornate workflow terms unless it is part of marketing or branding
