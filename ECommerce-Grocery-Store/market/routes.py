from http.client import HTTPResponse
from xml.dom.expatbuilder import FragmentBuilder
from flask import flash, redirect, render_template, request, url_for
from pyparsing import nums
from market import my_sql
from market import app
import random
from datetime import datetime,date

MARKETPLACE_DB = "comp7640_marketplace"

cart_id=0
total_val=0
total_count=0
customer_cart_list=[]


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


def get_marketplace_products(search_term=None):
    query = _build_product_search_query()
    params = None
    if search_term:
        query += """
        WHERE LOWER(p.product_name) LIKE %s
           OR LOWER(pt.tag_value) LIKE %s
        """
        like_term = f"%{search_term.lower()}%"
        params = (like_term, like_term)
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
    cur.execute(query, params)
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
            p.status
        FROM {MARKETPLACE_DB}.product AS p
        LEFT JOIN {MARKETPLACE_DB}.product_tag AS pt
            ON p.product_id = pt.product_id
        WHERE p.vendor_id = %s
        GROUP BY
            p.product_id,
            p.product_name,
            p.listed_price,
            p.stock_quantity,
            p.status
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
        })
    return products


def create_vendor(first_name, last_name, email, password, contact_number, geographical_presence):
    business_name = f"{first_name} {last_name}".strip()
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        INSERT INTO {MARKETPLACE_DB}.vendor
        (business_name, contact_person, email, contact_number, password_hash, geographical_presence, created_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), 'active')
        """,
        (business_name, first_name, email, contact_number, password, geographical_presence),
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


def create_customer(full_name, email, password, contact_number, shipping_address):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        INSERT INTO {MARKETPLACE_DB}.customer
        (full_name, email, contact_number, shipping_address, password_hash, created_at, status)
        VALUES (%s, %s, %s, %s, %s, NOW(), 'active')
        """,
        (full_name, email, contact_number, shipping_address, password),
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


def create_marketplace_order(customer_id, shipping_address, payment_method, grouped_items):
    total_price = compute_order_total(grouped_items)
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        INSERT INTO {MARKETPLACE_DB}.orders
        (customer_id, order_date, total_price, status, shipping_address)
        VALUES (%s, NOW(), %s, 'placed', %s)
        """,
        (customer_id, total_price, shipping_address),
    )
    order_id = cur.lastrowid

    for item in grouped_items:
        cur.execute(
            f"""
            INSERT INTO {MARKETPLACE_DB}.order_item
            (order_id, product_id, vendor_id, quantity, unit_price, subtotal, item_status)
            VALUES (%s, %s, %s, %s, %s, %s, 'placed')
            """,
            (
                order_id,
                item["ProductID"],
                item["VendorID"],
                item["Quantity"],
                item["Price"],
                item["Subtotal"],
            ),
        )
        cur.execute(
            f"""
            UPDATE {MARKETPLACE_DB}.product
            SET stock_quantity = stock_quantity - %s
            WHERE product_id = %s
            """,
            (item["Quantity"], item["ProductID"]),
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

    my_sql.connection.commit()
    cur.close()
    return order_id, total_price


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


def cancel_marketplace_order(order_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"SELECT customer_id, status FROM {MARKETPLACE_DB}.orders WHERE order_id = %s",
        (order_id,),
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


def remove_marketplace_order_item(order_id, order_item_id):
    cur = my_sql.connection.cursor()
    cur.execute(
        f"""
        SELECT customer_id, status
        FROM {MARKETPLACE_DB}.orders
        WHERE order_id = %s
        """,
        (order_id,),
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

@app.route('/admin/<admin_id>')
def adminRedirect(admin_id):
    return render_template('adminOption.html',admin_id=admin_id)

@app.route('/adminOrder/<admin_id>',methods=['GET', 'POST'])
def adminViewOrder(admin_id):
    my_list =[]
    cur = my_sql.connection.cursor()
    order_list = cur.execute("SELECT * FROM orders")
    if order_list>0:
        order_all = cur.fetchall()
        for order in order_all:
            temp_dict = {}
            for index in range(11):
                if(index==0):
                    temp_dict['Order_ID']=order[0]
                elif(index==1):
                    temp_dict['Mode']=order[1]
                elif(index==2):
                    temp_dict['Amount']=order[2]
                elif(index==9):
                    temp_dict['Date']=order[9]
            my_list.append(temp_dict)
    if request.method=='POST':
        return redirect('/admin/'+str(admin_id))
    return render_template('viewOrder.html',list=my_list)

@app.route('/adminOffer/<admin_id>',methods=['GET', 'POST'])
def adminAddOffer(admin_id):
    if request.method=='POST':
        offerDetails = request.form
        PC = offerDetails['Promo_Code']
        PD = offerDetails['Percentage_Discount']
        min_orderval = offerDetails['Min_OrderValue']
        max_discount = offerDetails['Max_Discount']
        cur = my_sql.connection.cursor()
        cur.execute("INSERT INTO offer(Promo_Code,Percentage_Discount,Min_OrderValue,Max_Discount,admin_id) VALUES(%s, %s, %s, %s,%s)",(PC,PD,min_orderval,max_discount,admin_id))
        flash('You have successfully added a Offer !')
        my_sql.connection.commit()
        cur.close()
    return render_template('addOffer.html',admin_id=admin_id)

@app.route('/adminDelivery_boy/<admin_id>',methods=['GET', 'POST'])
def adminAdd_Delivery_Boy(admin_id):
    if request.method=='POST':
        delivery_boy_Details = request.form
        First_Name = delivery_boy_Details['First_Name']
        Last_Name = delivery_boy_Details['Last_Name']
        Mobile_No = delivery_boy_Details['Mobile_No']
        Email = delivery_boy_Details['Email']
        Password = delivery_boy_Details['Password']
        cur = my_sql.connection.cursor()
        cur.execute("INSERT INTO delivery_boy(First_Name,Last_Name,Mobile_No,Email,Password,Average_Rating,Admin_ID) VALUES(%s, %s, %s, %s, %s,%s,%s)",(First_Name,Last_Name,Mobile_No,Email,Password,None,admin_id))
        flash('You have successfully added a delivery boy !')
        my_sql.connection.commit()
        cur.close()
    return render_template('addDelivery.html',admin_id=admin_id)

@app.route('/adminSeller/<admin_id>',methods=['GET', 'POST'])
def adminAdd_Seller(admin_id):
    if request.method=='POST':
        Seller_Details = request.form
        First_Name = Seller_Details['First_Name']
        Last_Name = Seller_Details['Last_Name']
        Email = Seller_Details['Email']
        Phone_Number = Seller_Details['Phone_Number']
        Password = Seller_Details['Password']
        Place_Of_Operation = Seller_Details['Place_Of_Operation']
        cur = my_sql.connection.cursor()
        cur.execute("INSERT INTO seller(First_Name,Last_Name,Email,Phone_Number,Password,Place_Of_Operation,Admin_ID) VALUES(%s, %s, %s, %s, %s,%s,%s)",(First_Name,Last_Name,Email,Phone_Number,Password,Place_Of_Operation,admin_id))
        flash('You have successfully added a seller !')
        my_sql.connection.commit()
        cur.close()
    return render_template('addSeller.html',admin_id=admin_id)

@app.route('/adminProduct/<admin_id>',methods=['GET', 'POST'])
def adminAdd_Product(admin_id):
    if request.method=='POST':
        Product_Details = request.form
        Name = Product_Details['Name']
        Price = Product_Details['Price']
        Brand= Product_Details['Brand']
        Measurement = Product_Details['Measurement']
        Category_ID = Product_Details['Category_ID']
        Unit = Product_Details['Unit']
        cur = my_sql.connection.cursor()
        cur.execute("INSERT INTO product(Name,Price,Brand,Measurement,Admin_ID,Category_ID,Unit) VALUES(%s, %s, %s, %s, %s,%s,%s)",(Name,Price,Brand,Measurement,admin_id,Category_ID,Unit))
        flash('You have successfully added a Product !')
        my_sql.connection.commit()
        cur.close()
    return render_template('addNewProducts.html',admin_id=admin_id)

@app.route('/sell/<seller_id>',methods=['GET', 'POST'])
def sell(seller_id):
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
            flash('Product added successfully to marketplace inventory')
        except ValueError:
            flash('Invalid product price, stock, or tag count')
        finally:
            cur.close()
        product_list = get_vendor_products(seller_id)
    return render_template('addProduct.html', products=product_list, vendor_id=seller_id)



def reinitialize():
    global cart_id
    global total_count
    global total_val
    global customer_cart_list
    cart_id = StaticClass.giveCartId()
    total_val=0
    total_count=0
    customer_cart_list=[]

@app.route('/home/<user_id>', methods=['GET', 'POST'])
def userEnter(user_id):
    my_list =[]
    global cart_id
    global total_count
    global total_val
    global customer_cart_list
    search_term = request.args.get("q", "").strip()
    my_list = get_marketplace_products(search_term or None)
    if request.method=='POST':
        cur = my_sql.connection.cursor()
        OID = 3
        f_amt = total_val
        cur.execute("INSERT INTO cart(Cart_ID,Total_Value,Total_Count,Offer_ID,Final_Amount) VALUES(%s, %s, %s, %s, %s)",(cart_id,total_val,total_count,OID,f_amt))
        my_sql.connection.commit()
        cur.close()
        url_direct = '/order'+'/'+str(user_id)
        return redirect(url_direct)
    else:
        purchaseDetails = request.args
        try:
            product_id = int(purchaseDetails['product_id'])
            product_row = get_marketplace_product_by_id(product_id)
            if product_row is None:
                raise KeyError
            Name = product_row[1]
            Brand = product_row[3]
            Price = float(product_row[2])
            VendorID = int(product_row[4])
            total_count=total_count+1
            total_val=total_val+Price
            temp_dict = {}
            temp_dict['Name']=Name
            temp_dict['Brand']=Brand 
            temp_dict['Price']=Price
            temp_dict['ProductID']=product_id
            temp_dict['VendorID']=VendorID
            customer_cart_list.append(temp_dict)
            flash('Product has been added successfully to the cart !')
        except (KeyError, TypeError, ValueError):
            pass
    return render_template('home.html',list=my_list, search_term=search_term)

@app.route('/order/<user_id>',methods=['GET','POST'])
def placeOrder(user_id):
    global customer_cart_list
    global cart_id
    global total_val 
    if request.method=='POST':
        grouped_items = group_cart_items(customer_cart_list)
        total_val = sum(item["Subtotal"] for item in grouped_items)
        return redirect('/placeOrder'+'/'+str(user_id))
    return render_template('order.html',list=customer_cart_list)

@app.route('/HomePage')
@app.route('/')
def homePage():
    return render_template('homepage.html')


@app.route('/myOrders/<user_id>', methods=['GET'])
def myOrders(user_id):
    orders = get_customer_orders(int(user_id))
    return render_template('customerOrders.html', orders=orders, user_id=user_id)

@app.route('/loginRegisterSeller')
def loginRegisterSeller():
    return render_template('loginregisterSeller.html')

@app.route('/loginRegisterUser')
def loginRegisterUser():
    return render_template('loginregisterUser.html')

@app.route('/loginRegisterAdmin')
def loginRegisterAdmin():
    return render_template('loginregisterAdmin.html')

@app.route('/placeOrder/<user_id>',methods=['GET','POST'])
def order_placing(user_id):
    global total_val
    global customer_cart_list
    if request.method=='POST':
        orderDetails = request.form
        HNO = orderDetails['HNO']
        City = orderDetails['City']
        State = orderDetails['State']
        Pincode = orderDetails['Pincode']
        Mode = orderDetails['Mode']
        shipping_address = f"{HNO}, {City}, {State}, {Pincode}"
        grouped_items = group_cart_items(customer_cart_list)
        _, total_val = create_marketplace_order(int(user_id), shipping_address, Mode, grouped_items)
        flash('Your Order has been placed Successfully !')
        customer_cart_list = []
        reinitialize()
        return redirect('/myOrders/' + str(user_id))
    return render_template('orderDetails.html',total_val=total_val)


@app.route('/cancelOrder/<user_id>/<order_id>', methods=['POST'])
def cancelOrder(user_id, order_id):
    if cancel_marketplace_order(int(order_id)):
        flash('Order cancelled successfully.')
    else:
        flash('Order can no longer be cancelled.')
    return redirect('/myOrders/' + str(user_id))


@app.route('/removeOrderItem/<user_id>/<order_id>/<order_item_id>', methods=['POST'])
def removeOrderItem(user_id, order_id, order_item_id):
    if remove_marketplace_order_item(int(order_id), int(order_item_id)):
        flash('Order item removed successfully.')
    else:
        flash('Order item can no longer be modified.')
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
        flash('You have registered successfully !')
    return render_template('customerRegister.html')

@app.route('/adminRegister',methods=['GET','POST'])
def adminRegister():
    if request.method=='POST':
        custDetails = request.form
        First_Name = custDetails['First_Name']
        Last_Name = custDetails['Last_Name']
        Password = custDetails['Password']
        cur = my_sql.connection.cursor()
        cur.execute("INSERT INTO admin(First_Name,Last_Name,Admin_Password) VALUES(%s, %s, %s)",(First_Name,Last_Name,Password))
        flash('You have registered successfully !')
        my_sql.connection.commit()
        cur.close()
    return render_template('adminRegister.html')

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
        flash('You have registered successfully as a vendor!')
    return render_template('sellerRegister.html')
        
@app.route('/UserLogin',methods=['GET','POST'])
def UserLogin():
    if request.method=='POST':
        userDetail = request.form
        Email = userDetail['Email']
        Password = userDetail['Password']
        c_tup = find_customer_login(Email)
        if c_tup is None or Password != c_tup[5]:
            flash('Invalid Email or Password')
        else:
            reinitialize()
            url_direct = '/home'+'/'+str(c_tup[0])
            return redirect(url_direct)
    return render_template('UserLogin.html')

@app.route('/AdminLogin',methods=['GET','POST'])
def AdminLogin():
    if request.method=='POST':
        userDetail = request.form
        First_Name = userDetail['First_Name']
        Last_Name = userDetail['Last_Name']
        Password = userDetail['Password']
        cur = my_sql.connection.cursor()
        cust_list = cur.execute("SELECT * FROM admin")
        if cust_list>0:
            cust_all = cur.fetchall()
            c_tup = ()
            for tup in cust_all:
                if(tup[1]==First_Name and tup[2]==Last_Name):
                    c_tup = tup
                    break
            if c_tup==() or Password!=c_tup[3]:
                flash('Invalid Email or Password')
            else:
                url_direct = '/admin'+'/'+str(c_tup[0])
                return redirect(url_direct)
    return render_template('AdminLogin.html')

@app.route('/SellerLogin',methods=['GET','POST'])
def SellerLogin():
    if request.method=='POST':
        userDetail = request.form
        Email = userDetail['Email']
        Password = userDetail['Password']
        c_tup = find_vendor_login(Email)
        if c_tup is None or Password != c_tup[5]:
            flash('Invalid Email or Password')
        else:
            url_direct = '/sell'+'/'+str(c_tup[0])
            return redirect(url_direct)
    return render_template('SellerLogin.html')

class StaticClass:
    
    cart_id = random.randint(1000,100000)

    @staticmethod
    def giveCartId():
        StaticClass.cart_id +=1
        return StaticClass.cart_id
