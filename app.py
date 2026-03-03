from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import urllib.parse
import os
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tailor_app_secret')

# GPay/payment information
GPAY_NUMBER = "8056561764"
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    # Psycopg 3 syntax
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    return conn

# Database setup (PostgreSQL Syntax)
def init_db():
    try:
        db = get_db()
        cur = db.cursor()
        
        # Customers Table
        cur.execute("""CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY, 
            name TEXT NOT NULL, 
            phone TEXT NOT NULL UNIQUE, 
            address TEXT)""")
        
        # Orders Table
        cur.execute("""CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY, 
            customer_id INTEGER NOT NULL REFERENCES customers(id), 
            garment_type TEXT NOT NULL, 
            status TEXT DEFAULT 'Pending', 
            price REAL NOT NULL, 
            due_date DATE NOT NULL, 
            measurements TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        
        # Inventory Table
        cur.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id SERIAL PRIMARY KEY,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            unit TEXT DEFAULT 'pcs',
            min_stock INTEGER DEFAULT 5)""")
        
        db.commit()
        cur.close()
        db.close()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database error: {e}")

@app.route("/")
def dashboard():
    db = get_db()
    cur = db.cursor()
    
    cur.execute("SELECT COUNT(*) FROM customers")
    c_count = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) FROM orders WHERE status != 'Delivered'")
    o_count = cur.fetchone()['count']
    
    cur.execute("SELECT SUM(price) FROM orders WHERE status='Delivered'")
    res = cur.fetchone()
    revenue = res['sum'] if res and res['sum'] else 0
    
    cur.execute("""SELECT o.*, c.name, c.phone FROM orders o 
                   JOIN customers c ON o.customer_id = c.id 
                   ORDER BY o.due_date ASC LIMIT 5""")
    recent = cur.fetchall()
    
    db.close()
    return render_template("index.html", 
                          stats={'c': c_count, 'o': o_count, 'r': revenue}, 
                          orders=recent, 
                          today=datetime.today().strftime('%Y-%m-%d'))

# ============ CUSTOMER ROUTES ============
@app.route("/customers")
def list_customers():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM customers ORDER BY name")
    customers = cur.fetchall()
    db.close()
    return render_template("customers.html", customers=customers)

@app.route("/customers/new", methods=['GET', 'POST'])
def new_customer():
    if request.method == 'POST':
        try:
            db = get_db()
            cur = db.cursor()
            cur.execute("INSERT INTO customers (name, phone, address) VALUES (%s, %s, %s)",
                       (request.form['name'], request.form['phone'], request.form['address']))
            db.commit()
            db.close()
            return redirect(url_for('list_customers'))
        except Exception as e:
            return render_template("customer_form.html", error="Phone number already exists or Error: " + str(e))
    return render_template("customer_form.html")

@app.route("/customer/<int:customer_id>")
def customer_profile(customer_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    customer = cur.fetchone()
    cur.execute("SELECT * FROM orders WHERE customer_id = %s ORDER BY due_date DESC", (customer_id,))
    orders = cur.fetchall()
    db.close()
    return render_template("customer_profile.html", customer=customer, orders=orders)

@app.route("/delete/customers/<int:customer_id>", methods=['POST', 'GET'])
def delete_customer(customer_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM orders WHERE customer_id = %s", (customer_id,))
    cur.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
    db.commit()
    db.close()
    return redirect(url_for('list_customers'))

# ============ ORDER ROUTES ============
@app.route("/orders")
def list_orders():
    db = get_db()
    cur = db.cursor()
    cur.execute("""SELECT o.*, c.name, c.phone FROM orders o 
                   JOIN customers c ON o.customer_id = c.id 
                   ORDER BY o.due_date ASC""")
    orders = cur.fetchall()
    db.close()
    return render_template("orders_list.html", orders=orders)

@app.route("/order/new", methods=['GET', 'POST'])
def new_order():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        measurements = []
        fields = ['length', 'chest', 'waist', 'hip', 'shoulder', 'sleeve', 'neck', 'thigh', 'inseam']
        for field in fields:
            val = request.form.get(field, '').strip()
            if val and val != '0':
                measurements.append(f"{field.capitalize()}: {val}\"")
        
        measure = " | ".join(measurements) if measurements else "No measurements added"
        cur.execute("""INSERT INTO orders (customer_id, garment_type, price, due_date, measurements, status) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (request.form['customer_id'], request.form['garment_type'], 
                     request.form['price'], request.form['due_date'], measure, 'Pending'))
        db.commit()
        db.close()
        return redirect(url_for('list_orders'))
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, name, phone FROM customers ORDER BY name")
    customers = cur.fetchall()
    db.close()
    return render_template("new_order.html", customers=customers)

@app.route("/order/<int:order_id>/edit", methods=['GET', 'POST'])
def edit_order(order_id):
    db = get_db()
    cur = db.cursor()
    if request.method == 'POST':
        new_status = request.form.get('status')
        cur.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id))
        db.commit()
        db.close()
        return redirect(url_for('list_orders'))
    
    cur.execute("""SELECT o.*, c.name, c.phone FROM orders o 
                   JOIN customers c ON o.customer_id = c.id 
                   WHERE o.id = %s""", (order_id,))
    order = cur.fetchone()
    db.close()
    return render_template("order_form.html", order=order)

@app.route("/order/<int:order_id>/bill")
def bill(order_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("""SELECT o.*, c.name, c.phone, c.address FROM orders o 
                   JOIN customers c ON o.customer_id = c.id 
                   WHERE o.id = %s""", (order_id,))
    order = cur.fetchone()
    db.close()
    return render_template("bill.html", order=order, gpay_number=GPAY_NUMBER)

@app.route("/delete/orders/<int:order_id>", methods=['POST', 'GET'])
def delete_order(order_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM orders WHERE id = %s", (order_id,))
    db.commit()
    db.close()
    return redirect(url_for('list_orders'))

# ============ WHATSAPP ROUTE ============
@app.route("/whatsapp/bill/<int:order_id>")
def whatsapp_bill(order_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("""SELECT o.*, c.name, c.phone FROM orders o 
                   JOIN customers c ON o.customer_id = c.id 
                   WHERE o.id = %s""", (order_id,))
    order = cur.fetchone()
    db.close()

    if not order: return redirect(url_for('list_orders'))

    message = (f"Hi {order['name']},\nYour order #{order['id']} ({order['garment_type']}) is ready.\n"
               f"Amount: ₹{order['price']}\nGPay: {GPAY_NUMBER}\nThank you!")
    
    phone = str(order['phone']).strip()
    if len(phone) == 10: phone = '91' + phone
    
    return redirect(f"https://wa.me/{phone}?text={urllib.parse.quote(message)}")

# ============ INVENTORY & RECEIPTS ============
@app.route("/inventory")
def inventory():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM inventory ORDER BY item_name")
    items = cur.fetchall()
    db.close()
    return render_template("inventory.html", items=items)

@app.route("/inventory/add", methods=['GET', 'POST'])
def add_inventory():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO inventory (item_name, quantity, unit, min_stock) VALUES (%s, %s, %s, %s)",
                  (request.form['item_name'], request.form['quantity'], request.form['unit'], request.form['min_stock']))
        db.commit()
        db.close()
        return redirect(url_for('inventory'))
    return render_template("inventory_form.html")

@app.route("/receipt")
def receipt():
    db = get_db()
    cur = db.cursor()
    cur.execute("""SELECT o.*, c.name FROM orders o 
                   JOIN customers c ON o.customer_id = c.id 
                   WHERE o.status = 'Delivered' 
                   ORDER BY o.id DESC LIMIT 10""")
    rows = cur.fetchall()
    total_revenue = sum(float(r['price']) for r in rows if r['price'])
    db.close()
    return render_template("receipt.html", orders=rows, total_revenue=total_revenue)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)