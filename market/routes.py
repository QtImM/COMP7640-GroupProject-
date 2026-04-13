from flask import flash, redirect, render_template, request, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from market import my_sql
from market import app
from market.translations import get_text

MARKETPLACE_DB = "comp7640_marketplace"

def get_customer_cart_items(customer_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT 
            ci.cart_item_id,
            ci.product_id,
            p.product_name,
            p.listed_price,
            v.vendor_id,
            v.business_name,
            ci.quantity
        FROM {MARKETPLACE_DB}.cart_item AS ci
        JOIN {MARKETPLACE_DB}.product AS p ON ci.product_id = p.product_id
        JOIN {MARKETPLACE_DB}.vendor AS v ON p.vendor_id = v.vendor_id
        WHERE ci.customer_id = %s
        """
        ,(customer_id,)
    )
    rows = cur.fetchall()
    cur.close()

    cart_items = []
    for row in rows:
        cart_items.append({
            "CartItemID": row[0],
            "ProductID": row[1],
            "Name": row[2],
            "Price": float(row[3]),
            "VendorID": row[4],
            "Vendor": row[5],
            "Quantity": row[6],
            "Subtotal": float(row[3]) * row[6],
        })
    return cart_items

def get_customer_cart_total(customer_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT SUM(p.listed_price * ci.quantity)
        FROM {MARKETPLACE_DB}.cart_item AS ci
        JOIN {MARKETPLACE_DB}.product AS p ON ci.product_id = p.product_id
        WHERE ci.customer_id = %s
        """
        ,(customer_id,)
    )
    total = cur.fetchone()[0] or 0.0
    cur.close()
    return float(total)

def clear_customer_cart(customer_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"DELETE FROM {MARKETPLACE_DB}.cart_item WHERE customer_id = %s",
        (customer_id,),
    )
    my_sql.connection.commit()
    cur.close()

def add_to_cart_db(customer_id, product_id):
    cur = my_sql.connection.cursor()
    # 1. Fetch current stock to see if it's available at all
    cur.execute(
        f"SELECT stock_quantity FROM {MARKETPLACE_DB}.product WHERE product_id = %s",
        (product_id,)
    )
    stock_row = cur.fetchone()
    if not stock_row or stock_row[0] <= 0:
        cur.close()
        return False, get_text('msg_out_of_stock', session.get('lang', 'en'))

    # 2. Add or update cart. No atomic stock deduction here yet (only on checkout)
    # but we should still check if cart qty exceeds stock
    cur.execute(
        f"SELECT cart_item_id, quantity FROM {MARKETPLACE_DB}.cart_item WHERE customer_id = %s AND product_id = %s",
        (customer_id, product_id)
    )
    row = cur.fetchone()
    
    if row:
        if row[1] + 1 > stock_row[0]:
            cur.close()
            return False, get_text('msg_stock_limit', session.get('lang', 'en'))
        cur.execute(
            f"UPDATE {MARKETPLACE_DB}.cart_item SET quantity = quantity + 1 WHERE cart_item_id = %s",
            (row[0],)
        )
    else:
        cur.execute(
            f"INSERT INTO {MARKETPLACE_DB}.cart_item (customer_id, product_id, quantity) VALUES (%s, %s, 1)",
            (customer_id, product_id)
        )
    my_sql.connection.commit()
    cur.close()
    return True, get_text('msg_added_to_cart', session.get('lang', 'en'))


def _build_product_search_query():
    return f"""
        SELECT
            p.product_id,
            p.product_name,
            p.listed_price,
            p.stock_quantity,
            v.business_name,
            GROUP_CONCAT(DISTINCT pt.tag_value ORDER BY pt.tag_value SEPARATOR ','),
            p.description
        FROM {MARKETPLACE_DB}.product AS p
        JOIN {MARKETPLACE_DB}.vendor AS v
            ON p.vendor_id = v.vendor_id
        LEFT JOIN {MARKETPLACE_DB}.product_tag AS pt
            ON p.product_id = pt.product_id
    """


def get_marketplace_products(search_term=None, vendor_id=None):
    query = _build_product_search_query()
    conditions = []
    params = []
    if search_term:
        conditions.append("(LOWER(p.product_name) LIKE %s OR LOWER(pt.tag_value) LIKE %s)")
        like_term = f"%{search_term.lower()}%"
        params.extend([like_term, like_term])
    if vendor_id is not None:
        conditions.append("p.vendor_id = %s")
        params.append(vendor_id)
    if conditions:
        query += "\n        WHERE " + "\n          AND ".join(conditions)
    query += """
        GROUP BY
            p.product_id,
            p.product_name,
            p.listed_price,
            p.stock_quantity,
            v.business_name,
            p.description
        ORDER BY p.product_name
    """

    cur = my_sql.connection.cursor()
    cur.execute(query, tuple(params) if params else None)
    rows = cur.fetchall()
    cur.close()

    products = []
    for row in rows:
        tag_values = row[5].split(",") if row[5] else []
        products.append({
            "ProductID": row[0],
            "Name": row[1],
            "Price": float(row[2]),
            "Stock": row[3],
            "Vendor": row[4],
            "Tags": tag_values,
            "Description": row[6] or "",
        })
    return products


def get_marketplace_product_by_id(product_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT p.product_id, p.product_name, p.listed_price, v.business_name, v.vendor_id
        FROM {MARKETPLACE_DB}.product AS p
        JOIN {MARKETPLACE_DB}.vendor AS v
            ON p.vendor_id = v.vendor_id
        WHERE p.product_id = %s
        """,
        (product_id,),
    )
    row = cur.fetchone()
    cur.close()
    return row


def get_vendor_products(vendor_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT
            p.product_id,
            p.product_name,
            p.listed_price,
            p.stock_quantity,
            GROUP_CONCAT(DISTINCT pt.tag_value ORDER BY pt.tag_value SEPARATOR ','),
            p.status,
            p.description
        FROM {MARKETPLACE_DB}.product AS p
        LEFT JOIN {MARKETPLACE_DB}.product_tag AS pt
            ON p.product_id = pt.product_id
        WHERE p.vendor_id = %s
        GROUP BY
            p.product_id,
            p.product_name,
            p.listed_price,
            p.stock_quantity,
            p.status,
            p.description
        ORDER BY p.product_name
        """,
        (vendor_id,),
    )
    rows = cur.fetchall()
    cur.close()

    products = []
    for row in rows:
        products.append({
            "ProductID": row[0],
            "Name": row[1],
            "Price": float(row[2]),
            "Stock": row[3],
            "Tags": row[4].split(",") if row[4] else [],
            "Status": row[5],
            "Description": row[6] or "",
        })
    return products


def get_all_vendors():
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT
            v.vendor_id,
            v.business_name,
            v.geographical_presence,
            v.average_rating,
            COUNT(p.product_id) AS product_count
        FROM {MARKETPLACE_DB}.vendor AS v
        LEFT JOIN {MARKETPLACE_DB}.product AS p
            ON v.vendor_id = p.vendor_id
        GROUP BY
            v.vendor_id,
            v.business_name,
            v.geographical_presence,
            v.average_rating
        ORDER BY v.business_name
        """
    )
    rows = cur.fetchall()
    cur.close()

    vendors = []
    for row in rows:
        vendors.append({
            "VendorID": row[0],
            "BusinessName": row[1],
            "Location": row[2],
            "AverageRating": float(row[3]) if row[3] is not None else None,
            "ProductCount": row[4],
        })
    return vendors


def get_default_customer_id():
    cur = my_sql.connection.cursor()
    cur.execute(f"SELECT customer_id FROM {MARKETPLACE_DB}.customer ORDER BY customer_id LIMIT 1")
    row = cur.fetchone()
    cur.close()
    return row[0] if row else 1


def get_default_vendor_id():
    cur = my_sql.connection.cursor()
    cur.execute(f"SELECT vendor_id FROM {MARKETPLACE_DB}.vendor ORDER BY vendor_id LIMIT 1")
    row = cur.fetchone()
    cur.close()
    return row[0] if row else 1


def update_cart_item_qty(customer_id, product_id, new_qty):
    cur = my_sql.connection.cursor()
    if new_qty <= 0:
        cur.execute(
            f"DELETE FROM {MARKETPLACE_DB}.cart_item WHERE customer_id = %s AND product_id = %s",
            (customer_id, product_id),
        )
    else:
        cur.execute(
            f"SELECT stock_quantity FROM {MARKETPLACE_DB}.product WHERE product_id = %s",
            (product_id,)
        )
        stock_row = cur.fetchone()
        if stock_row and new_qty > stock_row[0]:
            cur.close()
            return False, get_text('msg_units_available', session.get('lang', 'en')).format(stock=stock_row[0])
        cur.execute(
            f"UPDATE {MARKETPLACE_DB}.cart_item SET quantity = %s WHERE customer_id = %s AND product_id = %s",
            (new_qty, customer_id, product_id),
        )
    my_sql.connection.commit()
    cur.close()
    return True, get_text('msg_cart_updated', session.get('lang', 'en'))


def remove_cart_item(customer_id, cart_item_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"DELETE FROM {MARKETPLACE_DB}.cart_item WHERE cart_item_id = %s AND customer_id = %s",
        (cart_item_id, customer_id),
    )
    my_sql.connection.commit()
    cur.close()


def get_product_detail(product_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT
            p.product_id, p.product_name, p.listed_price, p.stock_quantity,
            p.description, p.status,
            v.vendor_id, v.business_name, v.geographical_presence, v.average_rating,
            GROUP_CONCAT(DISTINCT pt.tag_value ORDER BY pt.tag_value SEPARATOR ',')
        FROM {MARKETPLACE_DB}.product AS p
        JOIN {MARKETPLACE_DB}.vendor AS v ON p.vendor_id = v.vendor_id
        LEFT JOIN {MARKETPLACE_DB}.product_tag AS pt ON p.product_id = pt.product_id
        WHERE p.product_id = %s
        GROUP BY p.product_id, p.product_name, p.listed_price, p.stock_quantity,
                 p.description, p.status, v.vendor_id, v.business_name,
                 v.geographical_presence, v.average_rating
        """,
        (product_id,),
    )
    row = cur.fetchone()
    cur.close()
    if row is None:
        return None
    return {
        "ProductID": row[0],
        "Name": row[1],
        "Price": float(row[2]),
        "Stock": row[3],
        "Description": row[4] or "",
        "Status": row[5],
        "VendorID": row[6],
        "VendorName": row[7],
        "VendorLocation": row[8],
        "VendorRating": float(row[9]) if row[9] is not None else None,
        "Tags": row[10].split(",") if row[10] else [],
    }


def get_browse_customer_id():
    if session.get('role') == 'customer':
        return session.get('user_id')
    return None


def get_recommendations(customer_id):
    cur = my_sql.connection.cursor()
    # Use the customer's historical order tags as the smallest possible
    # personalized signal for a recommendation section.
    cur.execute(
        f"""
        SELECT pt.tag_value
        FROM {MARKETPLACE_DB}.orders o
        JOIN {MARKETPLACE_DB}.order_item oi ON o.order_id = oi.order_id
        JOIN {MARKETPLACE_DB}.product_tag pt ON oi.product_id = pt.product_id
        WHERE o.customer_id = %s
        GROUP BY pt.tag_value
        ORDER BY COUNT(*) DESC
        LIMIT 3
        """,
        (customer_id,)
    )
    fav_tags = [row[0] for row in cur.fetchall()]
    
    products = []
    if fav_tags:
        # Recommend only when the customer has real history-based tags.
        placeholders = ', '.join(['%s'] * len(fav_tags))
        cur.execute(
            f"""
            SELECT DISTINCT
                p.product_id,
                p.product_name,
                p.listed_price,
                v.business_name,
                GROUP_CONCAT(DISTINCT pt2.tag_value ORDER BY pt2.tag_value SEPARATOR ',')
            FROM {MARKETPLACE_DB}.product p
            JOIN {MARKETPLACE_DB}.vendor v ON p.vendor_id = v.vendor_id
            JOIN {MARKETPLACE_DB}.product_tag pt ON p.product_id = pt.product_id
            LEFT JOIN {MARKETPLACE_DB}.product_tag pt2 ON p.product_id = pt2.product_id
            WHERE pt.tag_value IN ({placeholders})
              AND p.product_id NOT IN (
                  SELECT product_id FROM {MARKETPLACE_DB}.order_item oi
                  JOIN {MARKETPLACE_DB}.orders o ON oi.order_id = o.order_id
                  WHERE o.customer_id = %s
              )
              AND p.status = 'active'
            GROUP BY
                p.product_id,
                p.product_name,
                p.listed_price,
                v.business_name
            ORDER BY p.product_name
            LIMIT 4
            """,
            (*fav_tags, customer_id)
        )
        rows = cur.fetchall()
        for row in rows:
            products.append({
                "ProductID": row[0],
                "Name": row[1],
                "Price": float(row[2]),
                "Vendor": row[3],
                "Tags": row[4].split(",") if row[4] else [],
            })
             
    cur.close()
    return products


def create_vendor(first_name, last_name, email, password, contact_number, geographical_presence):
    business_name = f"{first_name} {last_name}".strip()
    hashed_pw = generate_password_hash(password)
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        INSERT INTO {MARKETPLACE_DB}.vendor
        (business_name, contact_person, email, contact_number, password_hash, geographical_presence, created_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), 'active')
        """,
        (business_name, first_name, email, contact_number, hashed_pw, geographical_presence),
    )
    my_sql.connection.commit()
    cur.close()


def find_vendor_login(email):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT vendor_id, business_name, contact_person, email, contact_number, password_hash
        FROM {MARKETPLACE_DB}.vendor
        WHERE email = %s
        """,
        (email,),
    )
    vendor = cur.fetchone()
    cur.close()
    return vendor


def find_customer_login(email):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT customer_id, full_name, email, contact_number, shipping_address, password_hash
        FROM {MARKETPLACE_DB}.customer
        WHERE email = %s
        """,
        (email,),
    )
    customer = cur.fetchone()
    cur.close()
    return customer


def find_vendor_login_by_id(vendor_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT vendor_id, business_name
        FROM {MARKETPLACE_DB}.vendor
        WHERE vendor_id = %s
        """,
        (vendor_id,),
    )
    vendor = cur.fetchone()
    cur.close()
    return vendor


def create_customer(full_name, email, password, contact_number, shipping_address):
    hashed_pw = generate_password_hash(password)
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        INSERT INTO {MARKETPLACE_DB}.customer
        (full_name, email, contact_number, shipping_address, password_hash, created_at, status)
        VALUES (%s, %s, %s, %s, %s, NOW(), 'active')
        """,
        (full_name, email, contact_number, shipping_address, hashed_pw),
    )
    my_sql.connection.commit()
    cur.close()


def group_cart_items(cart_items):
    grouped = {}
    for item in cart_items:
        product_id = item["ProductID"]
        if product_id not in grouped:
            grouped[product_id] = {
                "ProductID": product_id,
                "Name": item["Name"],
                "VendorID": item["VendorID"],
                "Vendor": item["Vendor"],
                "Price": float(item["Price"]),
                "Quantity": 0,
                "Subtotal": 0.0,
            }
        grouped[product_id]["Quantity"] += 1
        grouped[product_id]["Subtotal"] += float(item["Price"])
    return list(grouped.values())


def calculate_vendor_transaction_amounts(grouped_items):
    transaction_totals = {}
    for item in grouped_items:
        vendor_id = item["VendorID"]
        transaction_totals[vendor_id] = transaction_totals.get(vendor_id, 0.0) + float(item["Subtotal"])
    return transaction_totals


def can_modify_order(order_status):
    return order_status in ("placed", "processing")


def compute_order_total(items):
    return sum(float(item["Subtotal"]) for item in items)


def create_marketplace_order(customer_id, shipping_address, payment_method, cart_items):
    cur = my_sql.connection.cursor()
    try:
        # 1. Total price
        total_price = sum(item["Subtotal"] for item in cart_items)
        
        # 2. Insert main order
        cur.execute(
            f"""
            INSERT INTO {MARKETPLACE_DB}.orders
            (customer_id, order_date, total_price, status, shipping_address)
            VALUES (%s, NOW(), %s, 'placed', %s)
            """,
            (customer_id, total_price, shipping_address),
        )
        order_id = cur.lastrowid
        
        vendor_totals = {}
        
        # 3. Process items and deduct stock ATOMICALLY
        for item in cart_items:
            # ATOMIC UPDATE: Only update if stock is sufficient
            affected_rows = cur.execute(
                f"""
                UPDATE {MARKETPLACE_DB}.product 
                SET stock_quantity = stock_quantity - %s 
                WHERE product_id = %s AND stock_quantity >= %s
                """,
                (item["Quantity"], item["ProductID"], item["Quantity"])
            )
            
            if affected_rows == 0:
                # Stock ran out just now!
                raise ValueError(f"Insufficient stock for {item['Name']}")

            # Insert order item
            cur.execute(
                f"""
                INSERT INTO {MARKETPLACE_DB}.order_item
                (order_id, product_id, vendor_id, quantity, unit_price, subtotal, item_status)
                VALUES (%s, %s, %s, %s, %s, %s, 'placed')
                """,
                (order_id, item["ProductID"], item["VendorID"], item["Quantity"], item["Price"], item["Subtotal"]),
            )
            
            v_id = item["VendorID"]
            vendor_totals[v_id] = vendor_totals.get(v_id, 0.0) + item["Subtotal"]
        
        # 4. Transactions
        for v_id, amount in vendor_totals.items():
            cur.execute(
                f"""
                INSERT INTO {MARKETPLACE_DB}.vendor_transaction
                (order_id, customer_id, vendor_id, amount, payment_method, transaction_time, transaction_status)
                VALUES (%s, %s, %s, %s, %s, NOW(), 'paid')
                """,
                (order_id, customer_id, v_id, amount, payment_method),
            )
            
        my_sql.connection.commit()
        return order_id
    except Exception as e:
        my_sql.connection.rollback()
        raise e
    finally:
        cur.close()


def rebuild_vendor_transactions(cur, order_id, customer_id, payment_method, grouped_items):
    cur.execute(
        f"DELETE FROM {MARKETPLACE_DB}.vendor_transaction WHERE order_id = %s",
        (order_id,),
    )
    vendor_totals = calculate_vendor_transaction_amounts(grouped_items)
    for vendor_id, amount in vendor_totals.items():
        cur.execute(
            f"""
            INSERT INTO {MARKETPLACE_DB}.vendor_transaction
            (order_id, customer_id, vendor_id, amount, payment_method, transaction_time, transaction_status)
            VALUES (%s, %s, %s, %s, %s, NOW(), 'paid')
            """,
            (order_id, customer_id, vendor_id, amount, payment_method),
        )


def get_order_items(order_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT
            oi.order_item_id,
            oi.order_id,
            oi.product_id,
            oi.vendor_id,
            p.product_name,
            v.business_name,
            oi.quantity,
            oi.unit_price,
            oi.subtotal,
            oi.item_status
        FROM {MARKETPLACE_DB}.order_item AS oi
        JOIN {MARKETPLACE_DB}.product AS p
            ON oi.product_id = p.product_id
        JOIN {MARKETPLACE_DB}.vendor AS v
            ON oi.vendor_id = v.vendor_id
        WHERE oi.order_id = %s
        ORDER BY oi.order_item_id
        """,
        (order_id,),
    )
    rows = cur.fetchall()
    cur.close()
    items = []
    for row in rows:
        items.append({
            "OrderItemID": row[0],
            "OrderID": row[1],
            "ProductID": row[2],
            "VendorID": row[3],
            "Name": row[4],
            "Vendor": row[5],
            "Quantity": row[6],
            "Price": float(row[7]),
            "Subtotal": float(row[8]),
            "Status": row[9],
        })
    return items


def get_customer_orders(customer_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT order_id, order_date, total_price, status, shipping_address
        FROM {MARKETPLACE_DB}.orders
        WHERE customer_id = %s
        ORDER BY order_date DESC, order_id DESC
        """,
        (customer_id,),
    )
    rows = cur.fetchall()
    cur.close()
    orders = []
    for row in rows:
        items = get_order_items(row[0])
        orders.append({
            "OrderID": row[0],
            "OrderDate": row[1],
            "TotalPrice": float(row[2]),
            "Status": row[3],
            "ShippingAddress": row[4],
            "CanModify": can_modify_order(row[3]),
            "Items": items,
        })
    return orders


def cancel_marketplace_order(customer_id, order_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT customer_id, status
        FROM {MARKETPLACE_DB}.orders
        WHERE order_id = %s AND customer_id = %s
        """,
        (order_id, customer_id),
    )
    order_row = cur.fetchone()
    if order_row is None or not can_modify_order(order_row[1]):
        cur.close()
        return False

    items = get_order_items(order_id)
    for item in items:
        cur.execute(
            f"""
            UPDATE {MARKETPLACE_DB}.product
            SET stock_quantity = stock_quantity + %s
            WHERE product_id = %s
            """,
            (item["Quantity"], item["ProductID"]),
        )
    cur.execute(
        f"UPDATE {MARKETPLACE_DB}.order_item SET item_status = 'cancelled' WHERE order_id = %s",
        (order_id,),
    )
    cur.execute(
        f"UPDATE {MARKETPLACE_DB}.orders SET status = 'cancelled', total_price = 0 WHERE order_id = %s",
        (order_id,),
    )
    cur.execute(
        f"UPDATE {MARKETPLACE_DB}.vendor_transaction SET transaction_status = 'cancelled', amount = 0 WHERE order_id = %s",
        (order_id,),
    )
    my_sql.connection.commit()
    cur.close()
    return True


def remove_marketplace_order_item(customer_id, order_id, order_item_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT customer_id, status
        FROM {MARKETPLACE_DB}.orders
        WHERE order_id = %s AND customer_id = %s
        """,
        (order_id, customer_id),
    )
    order_row = cur.fetchone()
    if order_row is None or not can_modify_order(order_row[1]):
        cur.close()
        return False

    cur.execute(
        f"""
        SELECT product_id, vendor_id, quantity
        FROM {MARKETPLACE_DB}.order_item
        WHERE order_item_id = %s AND order_id = %s
        """,
        (order_item_id, order_id),
    )
    item_row = cur.fetchone()
    if item_row is None:
        cur.close()
        return False

    cur.execute(
        f"""
        UPDATE {MARKETPLACE_DB}.product
        SET stock_quantity = stock_quantity + %s
        WHERE product_id = %s
        """,
        (item_row[2], item_row[0]),
    )
    cur.execute(
        f"DELETE FROM {MARKETPLACE_DB}.order_item WHERE order_item_id = %s",
        (order_item_id,),
    )

    cur.execute(
        f"""
        SELECT product_id, vendor_id, quantity, unit_price, subtotal
        FROM {MARKETPLACE_DB}.order_item
        WHERE order_id = %s
        """,
        (order_id,),
    )
    remaining_rows = cur.fetchall()

    if not remaining_rows:
        cur.execute(
            f"UPDATE {MARKETPLACE_DB}.orders SET status = 'cancelled', total_price = 0 WHERE order_id = %s",
            (order_id,),
        )
        cur.execute(
            f"DELETE FROM {MARKETPLACE_DB}.vendor_transaction WHERE order_id = %s",
            (order_id,),
        )
    else:
        grouped_items = [
            {
                "ProductID": row[0],
                "VendorID": row[1],
                "Quantity": row[2],
                "Price": float(row[3]),
                "Subtotal": float(row[4]),
            }
            for row in remaining_rows
        ]
        total_price = compute_order_total(grouped_items)
        cur.execute(
            f"UPDATE {MARKETPLACE_DB}.orders SET total_price = %s WHERE order_id = %s",
            (total_price, order_id),
        )
        rebuild_vendor_transactions(cur, order_id, order_row[0], "Updated Order", grouped_items)

    my_sql.connection.commit()
    cur.close()
    return True

@app.route('/product/<int:product_id>', methods=['GET'])
def productDetail(product_id):
    product = get_product_detail(product_id)
    if product is None:
        flash(get_text('flash_product_not_found', session.get('lang', 'en')))
        return redirect(url_for('homePage'))
    user_id = session.get('user_id') if session.get('role') == 'customer' else None
    return render_template('productDetail.html', product=product, user_id=user_id)


@app.route('/addToCart/<int:user_id>', methods=['POST'])
def addToCart(user_id):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if not is_authenticated(user_id, 'customer'):
        message = get_text('flash_access_denied', session.get('lang', 'en'))
        if is_ajax:
            return jsonify({'success': False, 'message': message, 'redirect': url_for('UserLogin')}), 401
        flash(message)
        return redirect(url_for('UserLogin'))

    success = False
    message = get_text('flash_invalid_item', session.get('lang', 'en'))
    product_id = request.form.get('product_id', type=int)
    if product_id:
        success, message = add_to_cart_db(user_id, product_id)

    if is_ajax:
        return jsonify({'success': success, 'message': message})

    if message:
        flash(message)
    redirect_to = request.form.get('redirect_to', '')
    if redirect_to:
        return redirect(redirect_to)
    return redirect(url_for('homepage', user_id=user_id))


@app.route('/updateCartQty/<int:user_id>', methods=['POST'])
def updateCartQty(user_id):
    if not is_authenticated(user_id, 'customer'):
        flash(get_text('flash_access_denied', session.get('lang', 'en')))
        return redirect(url_for('UserLogin'))
    product_id = request.form.get('product_id', type=int)
    action = request.form.get('action', '')
    cur = my_sql.connection.cursor()
    cur.execute(
        f"SELECT quantity FROM {MARKETPLACE_DB}.cart_item WHERE customer_id = %s AND product_id = %s",
        (user_id, product_id)
    )
    row = cur.fetchone()
    cur.close()
    if row:
        current_qty = row[0]
        if action == 'increase':
            new_qty = current_qty + 1
        elif action == 'decrease':
            new_qty = current_qty - 1
        else:
            new_qty = current_qty
        if new_qty <= 0:
            cur2 = my_sql.connection.cursor()
            cur2.execute(
                f"DELETE FROM {MARKETPLACE_DB}.cart_item WHERE customer_id = %s AND product_id = %s",
                (user_id, product_id),
            )
            my_sql.connection.commit()
            cur2.close()
            flash(get_text('flash_item_removed', session.get('lang', 'en')))
        else:
            success, message = update_cart_item_qty(user_id, product_id, new_qty)
            flash(message)
    return redirect(url_for('placeOrder', user_id=user_id))


@app.route('/removeCartItem/<int:user_id>/<int:cart_item_id>', methods=['POST'])
def removeCartItem(user_id, cart_item_id):
    if not is_authenticated(user_id, 'customer'):
        flash(get_text('flash_access_denied', session.get('lang', 'en')))
        return redirect(url_for('UserLogin'))
    remove_cart_item(user_id, cart_item_id)
    flash(get_text('flash_item_removed', session.get('lang', 'en')))
    return redirect(url_for('placeOrder', user_id=user_id))


@app.route('/editProduct/<int:vendor_id>/<int:product_id>', methods=['POST'])
def editProduct(vendor_id, product_id):
    if not is_authenticated(vendor_id, 'vendor'):
        flash(get_text('flash_access_denied', session.get('lang', 'en')))
        return redirect(url_for('SellerLogin'))
    cur = my_sql.connection.cursor()
    try:
        name = request.form['Name']
        price = float(request.form['Price'])
        stock = int(request.form['Quantity'])
        description = request.form.get('Description', '')
        tags_raw = [t.strip() for t in request.form.get('Tags', '').split(',') if t.strip()]
        if stock < 0 or price < 0 or len(tags_raw) > 3:
            raise ValueError
        cur.execute(
            f"""
            UPDATE {MARKETPLACE_DB}.product
            SET product_name = %s, listed_price = %s, stock_quantity = %s, description = %s
            WHERE product_id = %s AND vendor_id = %s
            """,
            (name, price, stock, description, product_id, vendor_id),
        )
        cur.execute(
            f"DELETE FROM {MARKETPLACE_DB}.product_tag WHERE product_id = %s",
            (product_id,),
        )
        for tag in tags_raw:
            cur.execute(
                f"INSERT INTO {MARKETPLACE_DB}.product_tag (product_id, tag_value) VALUES (%s, %s)",
                (product_id, tag),
            )
        my_sql.connection.commit()
        flash(get_text('flash_product_updated', session.get('lang', 'en')))
    except (ValueError, KeyError):
        flash(get_text('flash_invalid_data', session.get('lang', 'en')))
    finally:
        cur.close()
    return redirect(url_for('sell', seller_id=vendor_id))


@app.route('/deleteProduct/<int:vendor_id>/<int:product_id>', methods=['POST'])
def deleteProduct(vendor_id, product_id):
    if not is_authenticated(vendor_id, 'vendor'):
        flash(get_text('flash_access_denied', session.get('lang', 'en')))
        return redirect(url_for('SellerLogin'))
    cur = my_sql.connection.cursor()
    cur.execute(
        f"UPDATE {MARKETPLACE_DB}.product SET status = 'inactive' WHERE product_id = %s AND vendor_id = %s",
        (product_id, vendor_id),
    )
    my_sql.connection.commit()
    cur.close()
    flash(get_text('flash_product_deactivated', session.get('lang', 'en')))
    return redirect(url_for('sell', seller_id=vendor_id))


@app.route('/sell/<seller_id>',methods=['GET', 'POST'])
def sell(seller_id):
    if not is_authenticated(seller_id, 'vendor'):
        flash(get_text('flash_access_denied', session.get('lang', 'en')))
        return redirect(url_for('SellerLogin'))
    
    vendor_data = find_vendor_login_by_id(int(seller_id))
    business_name = vendor_data[1] if vendor_data else "Vendor"
    product_list = get_vendor_products(seller_id)
    if request.method=='POST':
        ProdDetail = request.form
        Name = ProdDetail['Name']
        Price = ProdDetail['Price']
        Quantity = ProdDetail['Quantity']
        Description = ProdDetail.get('Description', '')
        Tags = [tag.strip() for tag in ProdDetail.get('Tags', '').split(',') if tag.strip()]
        cur = my_sql.connection.cursor()
        try:
            stock_quantity = int(Quantity)
            listed_price = float(Price)
            if stock_quantity < 0 or listed_price < 0 or len(Tags) > 3:
                raise ValueError
            cur.execute(
                f"""
                INSERT INTO {MARKETPLACE_DB}.product
                (vendor_id, product_name, listed_price, stock_quantity, description, status, created_at)
                VALUES (%s, %s, %s, %s, %s, 'active', NOW())
                """,
                (seller_id, Name, listed_price, stock_quantity, Description),
            )
            product_id = cur.lastrowid
            for tag in Tags:
                cur.execute(
                    f"INSERT INTO {MARKETPLACE_DB}.product_tag (product_id, tag_value) VALUES (%s, %s)",
                    (product_id, tag),
                )
            my_sql.connection.commit()
            flash(get_text('flash_product_added', session.get('lang', 'en')))
        except ValueError:
            flash(get_text('flash_invalid_data', session.get('lang', 'en')))
        finally:
            cur.close()
        product_list = get_vendor_products(seller_id)
    return render_template('addProduct.html', products=product_list, vendor_id=seller_id, business_name=business_name)


@app.route('/home/<user_id>', methods=['GET'])
def homepage(user_id):
    if not is_authenticated(user_id, 'customer'):
        flash(get_text('flash_access_denied', session.get('lang', 'en')))
        return redirect(url_for('UserLogin'))
    
    search_term = request.args.get("q", "").strip()
    vendor_filter_id = request.args.get("vendor_id", type=int)
    selected_vendor = None
    if vendor_filter_id is not None:
        vendor_row = find_vendor_login_by_id(vendor_filter_id)
        if vendor_row is not None:
            selected_vendor = {
                "VendorID": vendor_row[0],
                "BusinessName": vendor_row[1],
            }
    my_list = get_marketplace_products(search_term or None, vendor_filter_id)
    recommendations = get_recommendations(int(user_id))

    return render_template(
        'home.html',
        list=my_list,
        search_term=search_term,
        user_id=user_id,
        recommendations=recommendations,
        selected_vendor=selected_vendor,
        vendor_filter_id=vendor_filter_id,
    )

def get_vendor_incoming_orders(vendor_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT 
            oi.order_item_id,
            oi.order_id,
            o.order_date,
            p.product_name,
            oi.quantity,
            oi.subtotal,
            oi.item_status,
            c.full_name,
            c.shipping_address
        FROM {MARKETPLACE_DB}.order_item oi
        JOIN {MARKETPLACE_DB}.orders o ON oi.order_id = o.order_id
        JOIN {MARKETPLACE_DB}.product p ON oi.product_id = p.product_id
        JOIN {MARKETPLACE_DB}.customer c ON o.customer_id = c.customer_id
        WHERE oi.vendor_id = %s
        ORDER BY o.order_date DESC
        """,
        (vendor_id,)
    )
    rows = cur.fetchall()
    cur.close()
    
    orders = []
    for row in rows:
        orders.append({
            "OrderItemID": row[0],
            "OrderID": row[1],
            "Date": row[2],
            "ProductName": row[3],
            "Quantity": row[4],
            "Amount": float(row[5]),
            "Status": row[6],
            "Customer": row[7],
            "Address": row[8]
        })
    return orders

@app.route('/vendorOrders/<vendor_id>', methods=['GET'])
def vendorOrders(vendor_id):
    if not is_authenticated(vendor_id, 'vendor'):
        flash(get_text('flash_access_denied', session.get('lang', 'en')))
        return redirect(url_for('SellerLogin'))
    orders = get_vendor_incoming_orders(int(vendor_id))
    return render_template('vendorOrders.html', orders=orders, vendor_id=vendor_id)

@app.route('/shipItem/<vendor_id>/<order_id>/<order_item_id>', methods=['POST'])
def shipItem(vendor_id, order_id, order_item_id):
    if not is_authenticated(vendor_id, 'vendor'):
        flash(get_text('flash_access_denied', session.get('lang', 'en')))
        return redirect(url_for('SellerLogin'))
    cur = my_sql.connection.cursor()

    # Resolve canonical order_id by owned order_item to prevent URL tampering.
    cur.execute(
        f"""
        SELECT order_id, item_status
        FROM {MARKETPLACE_DB}.order_item
        WHERE order_item_id = %s AND vendor_id = %s
        """,
        (order_item_id, vendor_id),
    )
    owned_item = cur.fetchone()
    if not owned_item:
        cur.close()
        flash(get_text('flash_invalid_item', session.get('lang', 'en')))
        return redirect(url_for('vendorOrders', vendor_id=vendor_id))

    canonical_order_id = int(owned_item[0])
    if owned_item[1] != 'placed':
        cur.close()
        flash(get_text('flash_status_error', session.get('lang', 'en')))
        return redirect(url_for('vendorOrders', vendor_id=vendor_id))

    cur.execute(
        f"UPDATE {MARKETPLACE_DB}.order_item SET item_status = 'shipped' WHERE order_item_id = %s AND vendor_id = %s",
        (order_item_id, vendor_id)
    )
    
    # Check if all items in the main order are shipped or cancelled
    cur.execute(
        f"SELECT COUNT(*) FROM {MARKETPLACE_DB}.order_item WHERE order_id = %s AND item_status = 'placed'",
        (canonical_order_id,)
    )
    remaining = cur.fetchone()[0]
    
    if remaining == 0:
        cur.execute(
            f"UPDATE {MARKETPLACE_DB}.orders SET status = 'shipped' WHERE order_id = %s",
            (canonical_order_id,)
        )
    else:
        cur.execute(
            f"UPDATE {MARKETPLACE_DB}.orders SET status = 'processing' WHERE order_id = %s",
            (canonical_order_id,)
        )
        
    my_sql.connection.commit()
    cur.close()
    flash(get_text('flash_shipped', session.get('lang', 'en')))
    return redirect(url_for('vendorOrders', vendor_id=vendor_id))

@app.route('/order/<user_id>', methods=['GET', 'POST'])
def placeOrder(user_id):
    if not is_authenticated(user_id, 'customer'):
        flash(get_text('flash_access_denied', session.get('lang', 'en')))
        return redirect(url_for('UserLogin'))
    cart_items = get_customer_cart_items(int(user_id))
    total_val = get_customer_cart_total(int(user_id))
    
    if request.method == 'POST':
        return redirect(url_for('order_placing', user_id=user_id))
        
    return render_template('order.html', list=cart_items, total_val=total_val, user_id=user_id)


@app.route('/vendors', methods=['GET'])
def vendorListing():
    vendors = get_all_vendors()
    browse_user_id = get_browse_customer_id()
    return render_template('vendors.html', vendors=vendors, browse_user_id=browse_user_id)


@app.route('/HomePage')
@app.route('/')
def homePage():
    return render_template('homepage.html')


@app.route('/myOrders/<user_id>', methods=['GET'])
def myOrders(user_id):
    if not is_authenticated(user_id, 'customer'):
        flash(get_text('flash_access_denied', session.get('lang', 'en')))
        return redirect(url_for('UserLogin'))
    orders = get_customer_orders(int(user_id))
    return render_template('customerOrders.html', orders=orders, user_id=user_id)

@app.route('/loginRegisterSeller')
def loginRegisterSeller():
    return render_template('loginregisterSeller.html')

@app.route('/loginRegisterUser')
def loginRegisterUser():
    return render_template('loginregisterUser.html')
    
@app.route('/placeOrder/<user_id>', methods=['GET', 'POST'])
def order_placing(user_id):
    if not is_authenticated(user_id, 'customer'):
        return redirect(url_for('UserLogin'))
    cart_items = get_customer_cart_items(int(user_id))
    
    total_val = get_customer_cart_total(int(user_id))

    if request.method == 'POST':
        orderDetails = request.form
        HNO = orderDetails['HNO']
        City = orderDetails['City']
        State = orderDetails['State']
        shipping_address = f"{HNO}, {City}, {State}"
        payment_method = 'standard'

        try:
            create_marketplace_order(int(user_id), shipping_address, payment_method, cart_items)
            flash(get_text('flash_order_success', session.get('lang', 'en')))
            clear_customer_cart(int(user_id))
            return redirect('/myOrders/' + str(user_id))
        except Exception as e:
            msg = get_text('flash_order_failed', session.get('lang', 'en')) + f": {str(e)}"
            flash(msg)
            return redirect('/order/' + str(user_id))

    return render_template('orderDetails.html', user_id=user_id, cart_items=cart_items, total_val=total_val)


@app.route('/cancelOrder/<user_id>/<order_id>', methods=['POST'])
def cancelOrder(user_id, order_id):
    if not is_authenticated(user_id, 'customer'):
        flash(get_text('flash_access_denied', session.get('lang', 'en')))
        return redirect(url_for('UserLogin'))
    if cancel_marketplace_order(int(user_id), int(order_id)):
        flash(get_text('flash_cancelled', session.get('lang', 'en')))
    else:
        flash(get_text('flash_status_error', session.get('lang', 'en')))
    return redirect('/myOrders/' + str(user_id))


@app.route('/removeOrderItem/<user_id>/<order_id>/<order_item_id>', methods=['POST'])
def removeOrderItem(user_id, order_id, order_item_id):
    if not is_authenticated(user_id, 'customer'):
        flash(get_text('flash_access_denied', session.get('lang', 'en')))
        return redirect(url_for('UserLogin'))
    if remove_marketplace_order_item(int(user_id), int(order_id), int(order_item_id)):
        flash(get_text('flash_item_removed', session.get('lang', 'en')))
    else:
        flash(get_text('flash_status_error', session.get('lang', 'en')))
    return redirect('/myOrders/' + str(user_id))

@app.route('/customerRegister',methods=['GET','POST'])
def customerRegister():
    if request.method=='POST':
        custDetails = request.form
        First_Name = custDetails['First_Name']
        Last_Name = custDetails['Last_Name']
        Email = custDetails['Email']
        Mobile_No = custDetails['Mobile_No']
        Password = custDetails['Password']
        Shipping_Address = custDetails['Shipping_Address']
        create_customer(f"{First_Name} {Last_Name}".strip(), Email, Password, Mobile_No, Shipping_Address)
        flash(get_text('flash_reg_success', session.get('lang', 'en')))
        return redirect(url_for('UserLogin'))
    return render_template('customerRegister.html')

@app.route('/sellerRegister',methods=['GET','POST'])
def sellerRegister():
    if request.method=='POST':
        sellerDetails = request.form
        First_Name = sellerDetails['First_Name']
        Last_Name = sellerDetails['Last_Name']
        Email = sellerDetails['Email']
        Password = sellerDetails['Password']
        Mobile_No = sellerDetails['Phone_Number']
        POO = sellerDetails['Place_Of_Operation']
        create_vendor(First_Name, Last_Name, Email, Password, Mobile_No, POO)
        flash(get_text('flash_reg_success', session.get('lang', 'en')))
        return redirect(url_for('SellerLogin'))
    return render_template('sellerRegister.html')
        
@app.route('/UserLogin',methods=['GET','POST'])
def UserLogin():
    if request.method=='POST':
        userDetail = request.form
        Email = userDetail['Email']
        Password = userDetail['Password']
        c_tup = find_customer_login(Email)
        if c_tup is None or not check_password_hash(c_tup[5], Password):
            flash(get_text('flash_login_invalid', session.get('lang', 'en')))
        else:
            # Clear previous session and set new identity
            session.clear()
            session['user_id'] = c_tup[0]
            session['role'] = 'customer'
            url_direct = '/home'+'/'+str(c_tup[0])
            return redirect(url_direct)
    return render_template('UserLogin.html')

@app.route('/SellerLogin',methods=['GET','POST'])
def SellerLogin():
    if request.method=='POST':
        userDetail = request.form
        Email = userDetail['Email']
        Password = userDetail['Password']
        c_tup = find_vendor_login(Email)
        if c_tup is None or not check_password_hash(c_tup[5], Password):
            flash(get_text('flash_login_invalid', session.get('lang', 'en')))
        else:
            # Clear previous session and set new identity
            session.clear()
            session['vendor_id'] = c_tup[0]
            session['role'] = 'vendor'
            url_direct = '/sell'+'/'+str(c_tup[0])
            return redirect(url_direct)
    return render_template('SellerLogin.html')

@app.route('/logout')
def logout():
    session.clear()
    flash(get_text('flash_logout_success', session.get('lang', 'en')))
    return redirect(url_for('homePage'))

def is_authenticated(required_id, role):
    """
    Strict session verification helper. 
    Protects against IDOR (Insecure Direct Object Reference).
    """
    if role == 'customer':
        return session.get('role') == 'customer' and session.get('user_id') == int(required_id)
    if role == 'vendor':
        return session.get('role') == 'vendor' and session.get('vendor_id') == int(required_id)
    return False

# System Cleanup: Removed deprecated StaticClass and global reinitialize logic

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'zh']:
        session['lang'] = lang
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect(url_for('homePage'))

