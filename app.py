from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from datetime import datetime
import urllib.parse
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tailor_app_secret')

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_SQLITE = not DATABASE_URL  # Use SQLite if DATABASE_URL not set

if USE_SQLITE:
    DB_PATH = 'tailor_pro.db'
else:
    import psycopg
    from psycopg.rows import dict_row


# Error handler for database/unavailable errors
@app.errorhandler(503)
def service_unavailable(error):
    return render_template('db_error.html', error=error.description if hasattr(error, 'description') else str(error)), 503

# GPay/payment information
GPAY_NUMBER = "8056561764"

def dict_from_row(row, cursor):
    """Convert SQLite row to dictionary"""
    if row is None:
        return None
    return dict(zip([col[0] for col in cursor.description], row))

def convert_sql(sql):
    """Convert SQL from psycopg (%s) to SQLite (?) syntax if needed"""
    if USE_SQLITE:
        return sql.replace('%s', '?')
    return sql

def execute_query(cur, sql, params=None):
    """Execute query with proper syntax for both SQLite and PostgreSQL"""
    if params:
        cur.execute(convert_sql(sql), params)
    else:
        cur.execute(sql)
    return cur

def fetchone_dict(cur):
    """Fetch one row and return as dict for both databases"""
    row = cur.fetchone()
    if row is None:
        return None
    if USE_SQLITE:
        return dict(row)
    return row

def fetchall_dict(cur):
    """Fetch all rows and return as list of dicts for both databases"""
    rows = cur.fetchall()
    if USE_SQLITE:
        return [dict(row) for row in rows]
    return rows

def get_db():
    try:
        if USE_SQLITE:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn
        else:
            conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5)
            return conn
    except Exception as e:
        print(f"[ERROR] Database Error: {e}")  # Debug output
        app.logger.exception("Failed to connect to the database")
        abort(503, description=f"Database connection failed: {str(e)}")

# Database setup
def init_db():
    try:
        db = get_db()
        cur = db.cursor()
        
        if USE_SQLITE:
            # SQLite syntax
            cur.execute("""CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT NOT NULL, 
                phone TEXT NOT NULL UNIQUE, 
                address TEXT)""")
            
            cur.execute("""CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                customer_id INTEGER NOT NULL,
                garment_type TEXT NOT NULL, 
                status TEXT DEFAULT 'Pending', 
                price REAL NOT NULL, 
                due_date DATE NOT NULL, 
                measurements TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id))""")
            
            cur.execute("""CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                unit TEXT DEFAULT 'pcs',
                min_stock INTEGER DEFAULT 5)""")
        else:
            # PostgreSQL syntax
            cur.execute("""CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY, 
                name TEXT NOT NULL, 
                phone TEXT NOT NULL UNIQUE, 
                address TEXT)""")
            
            cur.execute("""CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY, 
                customer_id INTEGER NOT NULL REFERENCES customers(id), 
                garment_type TEXT NOT NULL, 
                status TEXT DEFAULT 'Pending', 
                price REAL NOT NULL, 
                due_date DATE NOT NULL, 
                measurements TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            
            cur.execute("""CREATE TABLE IF NOT EXISTS inventory (
                id SERIAL PRIMARY KEY,
                item_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                unit TEXT DEFAULT 'pcs',
                min_stock INTEGER DEFAULT 5)""")
        
        db.commit()
        cur.close()
        db.close()
        print("[OK] Database initialized successfully!")
    except Exception as e:
        app.logger.exception("Database error during initialization")
        print(f"[WARN] Database error: {e}")

@app.route("/")
def dashboard():
    db = None
    try:
        db = get_db()
        cur = db.cursor()
        
        execute_query(cur, "SELECT COUNT(*) as count FROM customers")
        c_count = fetchone_dict(cur)['count']
        
        execute_query(cur, "SELECT COUNT(*) as count FROM orders WHERE status != 'Delivered'")
        o_count = fetchone_dict(cur)['count']
        
        execute_query(cur, "SELECT SUM(price) as sum FROM orders WHERE status='Delivered'")
        res = fetchone_dict(cur)
        revenue = res['sum'] if res and res['sum'] else 0
        
        execute_query(cur, """SELECT o.*, c.name, c.phone FROM orders o 
                       JOIN customers c ON o.customer_id = c.id 
                       ORDER BY o.due_date ASC LIMIT 5""")
        recent = fetchall_dict(cur)
        
        return render_template("index.html", 
                              stats={'c': c_count, 'o': o_count, 'r': revenue}, 
                              orders=recent, 
                              today=datetime.today().strftime('%Y-%m-%d'))
    except Exception as e:
        print(f"[ERROR in dashboard] {e}")
        import traceback
        traceback.print_exc()
        abort(503, description=f"Error: {str(e)}")
    finally:
        if db:
            db.close()

# ============ CUSTOMER ROUTES ============
@app.route("/customers")
def list_customers():
    db = get_db()
    cur = db.cursor()
    execute_query(cur, "SELECT * FROM customers ORDER BY name")
    customers = fetchall_dict(cur)
    db.close()
    return render_template("customers.html", customers=customers)

@app.route("/customers/new", methods=['GET', 'POST'])
def new_customer():
    if request.method == 'POST':
        try:
            db = get_db()
            cur = db.cursor()
            execute_query(cur, "INSERT INTO customers (name, phone, address) VALUES (%s, %s, %s)",
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
    execute_query(cur, "SELECT * FROM customers WHERE id = %s", (customer_id,))
    customer = fetchone_dict(cur)
    execute_query(cur, "SELECT * FROM orders WHERE customer_id = %s ORDER BY due_date DESC", (customer_id,))
    orders = fetchall_dict(cur)
    db.close()
    return render_template("customer_profile.html", customer=customer, orders=orders)

@app.route("/delete/customers/<int:customer_id>", methods=['POST', 'GET'])
def delete_customer(customer_id):
    db = get_db()
    cur = db.cursor()
    execute_query(cur, "DELETE FROM orders WHERE customer_id = %s", (customer_id,))
    execute_query(cur, "DELETE FROM customers WHERE id = %s", (customer_id,))
    db.commit()
    db.close()
    return redirect(url_for('list_customers'))

# ============ ORDER ROUTES ============
@app.route("/orders")
def list_orders():
    db = get_db()
    cur = db.cursor()
    execute_query(cur, """SELECT o.*, c.name, c.phone FROM orders o 
                   JOIN customers c ON o.customer_id = c.id 
                   ORDER BY o.due_date ASC""")
    orders = fetchall_dict(cur)
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
        execute_query(cur, """INSERT INTO orders (customer_id, garment_type, price, due_date, measurements, status) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (request.form['customer_id'], request.form['garment_type'], 
                     request.form['price'], request.form['due_date'], measure, 'Pending'))
        db.commit()
        db.close()
        return redirect(url_for('list_orders'))
    
    db = get_db()
    cur = db.cursor()
    execute_query(cur, "SELECT id, name, phone FROM customers ORDER BY name")
    customers = fetchall_dict(cur)
    db.close()
    return render_template("new_order.html", customers=customers)

@app.route("/order/<int:order_id>/edit", methods=['GET', 'POST'])
def edit_order(order_id):
    db = get_db()
    cur = db.cursor()
    if request.method == 'POST':
        new_status = request.form.get('status')
        execute_query(cur, "UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id))
        db.commit()
        db.close()
        return redirect(url_for('list_orders'))
    
    execute_query(cur, """SELECT o.*, c.name, c.phone FROM orders o 
                   JOIN customers c ON o.customer_id = c.id 
                   WHERE o.id = %s""", (order_id,))
    order = fetchone_dict(cur)
    db.close()
    return render_template("order_form.html", order=order)

@app.route("/order/<int:order_id>/bill")
def bill(order_id):
    db = get_db()
    cur = db.cursor()
    execute_query(cur, """SELECT o.*, c.name, c.phone, c.address FROM orders o 
                   JOIN customers c ON o.customer_id = c.id 
                   WHERE o.id = %s""", (order_id,))
    order = fetchone_dict(cur)
    db.close()
    return render_template("bill.html", order=order, gpay_number=GPAY_NUMBER)

@app.route("/delete/orders/<int:order_id>", methods=['POST', 'GET'])
def delete_order(order_id):
    db = get_db()
    cur = db.cursor()
    execute_query(cur, "DELETE FROM orders WHERE id = %s", (order_id,))
    db.commit()
    db.close()
    return redirect(url_for('list_orders'))

# ============ WHATSAPP ROUTE ============
@app.route("/whatsapp/bill/<int:order_id>")
def whatsapp_bill(order_id):
    db = get_db()
    cur = db.cursor()
    execute_query(cur, """SELECT o.*, c.name, c.phone FROM orders o 
                   JOIN customers c ON o.customer_id = c.id 
                   WHERE o.id = %s""", (order_id,))
    order = fetchone_dict(cur)
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
    execute_query(cur, "SELECT * FROM inventory ORDER BY item_name")
    items = fetchall_dict(cur)
    db.close()
    return render_template("inventory.html", items=items)

@app.route("/inventory/add", methods=['GET', 'POST'])
def add_inventory():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        execute_query(cur, "INSERT INTO inventory (item_name, quantity, unit, min_stock) VALUES (%s, %s, %s, %s)",
                  (request.form['item_name'], request.form['quantity'], request.form['unit'], request.form['min_stock']))
        db.commit()
        db.close()
        return redirect(url_for('inventory'))
    return render_template("inventory_form.html")

@app.route("/receipt")
def receipt():
    db = get_db()
    cur = db.cursor()
    execute_query(cur, """SELECT o.*, c.name FROM orders o 
                   JOIN customers c ON o.customer_id = c.id 
                   WHERE o.status = 'Delivered' 
                   ORDER BY o.id DESC LIMIT 10""")
    rows = fetchall_dict(cur)
    total_revenue = sum(float(r['price']) for r in rows if r['price'])
    db.close()
    return render_template("receipt.html", orders=rows, total_revenue=total_revenue)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)