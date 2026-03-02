from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime
import urllib.parse
import os

# Try to import pywhatkit for automatic WhatsApp messages
try:
    import pywhatkit as kit
    WHATSAPP_AVAILABLE = True
except Exception:
    kit = None
    WHATSAPP_AVAILABLE = False
    print("⚠️ pywhatkit not available — WhatsApp auto-send disabled.")

# GPay/payment information
GPAY_NUMBER = "8056561764"

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("tailor_pro.db")
    conn.row_factory = sqlite3.Row
    return conn

# Database setup
def init_db():
    db = get_db()
    db.execute("""CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT NOT NULL, 
        phone TEXT NOT NULL UNIQUE, 
        address TEXT)""")
    
    db.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        customer_id INTEGER NOT NULL, 
        garment_type TEXT NOT NULL, 
        status TEXT DEFAULT 'Pending', 
        price REAL NOT NULL, 
        due_date DATE NOT NULL, 
        measurements TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(customer_id) REFERENCES customers(id))""")
    
    cursor = db.execute("PRAGMA table_info(orders)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'created_at' not in cols:
        db.execute("ALTER TABLE orders ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    
    db.execute("""CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        quantity INTEGER DEFAULT 0,
        unit TEXT DEFAULT 'pcs',
        min_stock INTEGER DEFAULT 5)""")
    
    db.commit()
    db.close()

@app.route("/")
def dashboard():
    db = get_db()
    c_count = db.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    o_count = db.execute("SELECT COUNT(*) FROM orders WHERE status != 'Delivered'").fetchone()[0]
    revenue = db.execute("SELECT SUM(price) FROM orders WHERE status='Delivered'").fetchone()[0] or 0
    recent = db.execute("""SELECT o.*, c.name, c.phone FROM orders o 
                           JOIN customers c ON o.customer_id = c.id 
                           ORDER BY o.due_date ASC LIMIT 5""").fetchall()
    db.close()
    return render_template("index.html", 
                          stats={'c': c_count, 'o': o_count, 'r': revenue}, 
                          orders=recent, 
                          today=datetime.today().strftime('%Y-%m-%d'))

# ============ CUSTOMER ROUTES ============
@app.route("/customers")
def list_customers():
    db = get_db()
    customers = db.execute("SELECT * FROM customers ORDER BY name").fetchall()
    db.close()
    return render_template("customers.html", customers=customers)

@app.route("/customers/new", methods=['GET', 'POST'])
def new_customer():
    if request.method == 'POST':
        try:
            db = get_db()
            db.execute("""INSERT INTO customers (name, phone, address) 
                         VALUES (?, ?, ?)""",
                      (request.form['name'], request.form['phone'], request.form['address']))
            db.commit()
            db.close()
            return redirect(url_for('list_customers'))
        except sqlite3.IntegrityError:
            return render_template("customer_form.html", error="Phone number already exists!")
    return render_template("customer_form.html")

@app.route("/customer/<int:customer_id>")
def customer_profile(customer_id):
    db = get_db()
    customer = db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    orders = db.execute("SELECT * FROM orders WHERE customer_id = ? ORDER BY due_date DESC", (customer_id,)).fetchall()
    db.close()
    return render_template("customer_profile.html", customer=customer, orders=orders)

@app.route("/delete/customers/<int:customer_id>", methods=['POST', 'GET'])
def delete_customer(customer_id):
    db = get_db()
    db.execute("DELETE FROM orders WHERE customer_id = ?", (customer_id,))
    db.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    db.commit()
    db.close()
    return redirect(url_for('list_customers'))

# ============ ORDER ROUTES (Status & WhatsApp) ============

# 1. FIXED: Trigger WhatsApp when status is manually set to "Ready"
@app.route("/order/<int:order_id>/edit", methods=['GET', 'POST'])
def edit_order(order_id):
    db = get_db()
    if request.method == 'POST':
        new_status = request.form.get('status')
        db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        db.commit()

        # If order becomes Ready, attempt to send WhatsApp automatically (English message)
        if new_status == 'Ready':
            # fetch order details for message
            order = db.execute("""SELECT o.*, c.name, c.phone FROM orders o 
                                  JOIN customers c ON o.customer_id = c.id 
                                  WHERE o.id = ?""", (order_id,)).fetchone()
            db.close()

            if order and WHATSAPP_AVAILABLE:
                try:
                    phone = order['phone']
                    if not phone.startswith('+'):
                        phone = '+91' + phone
                    message = (
                        f"Hi {order['name']},\n\n"
                        f"Your order #{order['id']} ({order['garment_type']}) is ready for pickup.\n"
                        f"Amount: ₹{order['price']}\n"
                        f"Due Date: {order['due_date']}\n\n"
                        f"You can pay via GPay: {GPAY_NUMBER} or scan the QR on your bill.\n\n"
                        f"Thank you for choosing Mery Stitch & Style!"
                    )
                    kit.sendwhatmsg_instantly(phone, message)
                except Exception as e:
                    print(f"WhatsApp auto-send error: {e}")
            else:
                # if pywhatkit not available or order missing, do nothing — manual button remains
                pass

            return redirect(url_for('list_orders'))

        db.close()
        return redirect(url_for('list_orders'))
    
    order = db.execute("""SELECT o.*, c.name, c.phone FROM orders o 
                          JOIN customers c ON o.customer_id = c.id 
                          WHERE o.id = ?""", (order_id,)).fetchone()
    db.close()
    return render_template("order_form.html", order=order)

# 2. FIXED: This handles the WhatsApp icon in your table (orders_list.html)
@app.route("/whatsapp/<int:order_id>")
def whatsapp_msg(order_id):
    db = get_db()
    order = db.execute("""SELECT o.*, c.name, c.phone FROM orders o 
                          JOIN customers c ON o.customer_id = c.id 
                          WHERE o.id = ?""", (order_id,)).fetchone()
    db.close()
    
    message = (
        f"Hi {order['name']},\n\n"
        f"Here are your bill details:\n"
        f"Garment: {order['garment_type']}\n"
        f"Amount: ₹{order['price']}\n"
        f"Due Date: {order['due_date']}\n\n"
        f"You can pay via GPay: {GPAY_NUMBER} or scan the QR on your bill.\n\n"
        f"Thank you!"
    )
    return redirect(f"https://wa.me/91{order['phone']}?text={urllib.parse.quote(message)}")


@app.route("/whatsapp/bill/<int:order_id>")
def whatsapp_bill(order_id):
    """Send bill/payment details via WhatsApp (used from bill page button)"""
    db = get_db()
    order = db.execute("""SELECT o.*, c.name, c.phone FROM orders o 
                          JOIN customers c ON o.customer_id = c.id 
                          WHERE o.id = ?""", (order_id,)).fetchone()
    db.close()

    if not order:
        return redirect(url_for('list_orders'))

    message = (
        f"Hi {order['name']},\n\n"
        f"Here are your bill details:\n"
        f"Garment: {order['garment_type']}\n"
        f"Amount: ₹{order['price']}\n"
        f"Due Date: {order['due_date']}\n\n"
        f"You can pay via GPay: {GPAY_NUMBER} or scan the QR on your bill.\n\n"
        f"Thank you!"
    )

    phone = str(order['phone']).strip()
    # normalize phone for wa.me (no +, include country code)
    if phone.startswith('+'):
        phone = phone[1:]
    if phone.startswith('0'):
        phone = phone.lstrip('0')
    if len(phone) == 10:
        phone = '91' + phone

    return redirect(f"https://wa.me/{phone}?text={urllib.parse.quote(message)}")

@app.route("/orders")
def list_orders():
    db = get_db()
    orders = db.execute("""SELECT o.*, c.name, c.phone FROM orders o 
                           JOIN customers c ON o.customer_id = c.id 
                           ORDER BY o.due_date ASC""").fetchall()
    db.close()
    return render_template("orders_list.html", orders=orders)

@app.route("/order/new", methods=['GET', 'POST'])
def new_order():
    if request.method == 'POST':
        db = get_db()
        measurements = []
        fields = ['length', 'chest', 'waist', 'hip', 'shoulder', 'sleeve', 'neck', 'thigh', 'inseam']
        for field in fields:
            val = request.form.get(field, '').strip()
            if val and val != '0':
                measurements.append(f"{field.capitalize()}: {val}\"")
        
        measure = " | ".join(measurements) if measurements else "No measurements added"
        db.execute("""INSERT INTO orders (customer_id, garment_type, price, due_date, measurements, status) 
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (request.form['customer_id'], request.form['garment_type'], 
                   request.form['price'], request.form['due_date'], measure, 'Pending'))
        db.commit()
        db.close()
        return redirect(url_for('list_orders'))
    
    db = get_db()
    customers = db.execute("SELECT id, name, phone FROM customers ORDER BY name").fetchall()
    db.close()
    return render_template("new_order.html", customers=customers)

@app.route("/order/<int:order_id>/bill")
def bill(order_id):
    db = get_db()
    order = db.execute("""SELECT o.*, c.name, c.phone, c.address FROM orders o 
                          JOIN customers c ON o.customer_id = c.id 
                          WHERE o.id = ?""", (order_id,)).fetchone()
    db.close()
    return render_template("bill.html", order=order, gpay_number=GPAY_NUMBER)

@app.route("/delete/orders/<int:order_id>", methods=['POST', 'GET'])
def delete_order(order_id):
    db = get_db()
    db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    db.commit()
    db.close()
    return redirect(url_for('list_orders'))

# ============ INVENTORY & RECEIPTS ============
@app.route("/inventory")
def inventory():
    db = get_db()
    items = db.execute("SELECT * FROM inventory ORDER BY item_name").fetchall()
    db.close()
    return render_template("inventory.html", items=items)

@app.route("/inventory/add", methods=['GET', 'POST'])
def add_inventory():
    if request.method == 'POST':
        db = get_db()
        db.execute("INSERT INTO inventory (item_name, quantity, unit, min_stock) VALUES (?, ?, ?, ?)",
                  (request.form['item_name'], request.form['quantity'], request.form['unit'], request.form['min_stock']))
        db.commit()
        db.close()
        return redirect(url_for('inventory'))
    return render_template("inventory_form.html")

@app.route("/receipt")
def receipt():
    db = get_db()
    rows = db.execute("""SELECT o.*, c.name FROM orders o 
                          JOIN customers c ON o.customer_id = c.id 
                          WHERE o.status = 'Delivered' 
                          ORDER BY o.id DESC LIMIT 10""").fetchall()
    total_revenue = sum(float(r['price']) for r in rows if r['price'])
    db.close()
    return render_template("receipt.html", orders=rows, total_revenue=total_revenue)

if __name__ == "__main__":
    init_db()
    # Cloud-kaaga port-ah dynamic-ah edukanum
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)