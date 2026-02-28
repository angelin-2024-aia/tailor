# TailorPro - Tailor Shop Management System

## Overview
TailorPro is a complete web-based management system for tailor shops. It helps manage customers, orders, measurements, inventory, and generates bills/receipts.

## Features

### 📊 Dashboard
- Real-time statistics (Total customers, pending orders, revenue)
- Upcoming delivery schedule
- Quick action buttons

### 👥 Customer Management
- Add, view, and delete customers
- Customer profiles with order history
- Phone number tracking for WhatsApp integration

### 📋 Order Management
- Create new orders with customer measurements
- Track order status (Pending, In Progress, Ready, Delivered)
- Update order status
- View detailed measurements
- Generate bills and receipts

### 💬 WhatsApp Integration
- Send order status updates via WhatsApp
- Automatic message formatting with customer details

### 📦 Inventory Management
- Track materials and supplies
- Set minimum stock levels
- Add/remove inventory items
- Stock level monitoring

### 🧾 Billing System
- Generate professional bills/receipts
- QR code for payment
- Print-friendly format
- Daily register for delivered orders

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup Steps

1. **Clone/Download the project**
   ```bash
   cd d:\Backup\Tailor_app
   ```

2. **Create a Virtual Environment** (Optional but recommended)
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the Application**
   - Open your browser and go to: `http://127.0.0.1:5000`
   - Dashboard will load automatically

## Project Structure

```
tailor_app/
├── app.py                 # Flask application & routes
├── requirements.txt       # Python dependencies
├── tailor_pro.db         # SQLite database (auto-created)
├── static/
│   └── css/
│       └── style.css     # Application styling
└── templates/            # HTML templates
    ├── layout.html       # Base template
    ├── index.html        # Dashboard
    ├── customers.html    # Customer list
    ├── customer_form.html
    ├── customer_profile.html
    ├── orders_list.html  # All orders
    ├── new_order.html    # Create order
    ├── order_form.html   # Edit order
    ├── bill.html         # Bill/Receipt
    ├── inventory.html    # Stock management
    ├── inventory_form.html
    └── receipt.html      # Daily register
```

## Database Schema

### customers table
- id (PRIMARY KEY)
- name
- phone (UNIQUE)
- address

### orders table
- id (PRIMARY KEY)
- customer_id (FOREIGN KEY)
- garment_type
- status (Pending, In Progress, Ready, Delivered)
- price
- due_date
- measurements
- created_at

### inventory table
- id (PRIMARY KEY)
- item_name
- quantity
- unit
- min_stock

## Routes

### Dashboard & Home
- `GET /` - Dashboard

### Customer Management
- `GET /customers` - List all customers
- `GET /customers/new` - Add customer form
- `POST /customers/new` - Create customer
- `GET /customer/<id>` - Customer profile
- `GET /delete/customers/<id>` - Delete customer

### Order Management
- `GET /orders` - List all orders
- `GET /order/new` - Create order form
- `POST /order/new` - Create order
- `GET /order/<id>/edit` - Edit order form
- `POST /order/<id>/edit` - Update order
- `GET /order/<id>/bill` - View bill
- `GET /delete/orders/<id>` - Delete order

### Inventory
- `GET /inventory` - List inventory
- `GET /inventory/add` - Add inventory form
- `POST /inventory/add` - Create inventory item

### WhatsApp Integration
- `GET /whatsapp/<id>` - Send WhatsApp message for order

### Daily Register
- `GET /receipt` - View delivered orders and daily summary

## Usage

### Creating a Customer
1. Click "Customers" in navigation
2. Click "+ Add Customer"
3. Fill in name, phone, and address
4. Click "Save Customer"

### Creating an Order
1. Click "+ New Order" (Dashboard or Orders page)
2. Select customer from dropdown
3. Enter garment type and due date
4. Enter measurements (Length, Chest, Shoulder)
5. Enter bill amount
6. Click "Confirm Order"

### Updating Order Status
1. Go to Orders page
2. Click "Edit" on the order
3. Change status from dropdown
4. Click "Update Status"

### Generating Bill
1. Click "Bill" button on any order
2. View detailed bill with customer info
3. Click "Print" to print or save as PDF

### Sending WhatsApp Message
1. Click the WhatsApp icon on any order
2. System will send message to customer's registered phone

### Managing Inventory
1. Click "Inventory" in navigation
2. Click "+ Add Item"
3. Enter item name, quantity, unit, and minimum stock
4. Click "Add Item"

## Technical Details

### Technologies Used
- **Backend**: Flask (Python web framework)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, Bootstrap Icons
- **Integration**: PyWhatKit (WhatsApp messaging)

### Database Features
- Foreign key relationships
- Unique phone number constraints
- Automatic timestamps

### Security Notes
- Use strong passwords if deploying to production
- Configure CORS if accessing from different domains
- Enable HTTPS in production
- Add user authentication for multi-user scenarios

## Troubleshooting

### App won't start
- Ensure Python 3.8+ is installed
- Check if port 5000 is available
- Verify all dependencies are installed

### WhatsApp not working
- Ensure PyWhatKit is installed
- Check internet connection
- Phone number should include country code (+91 for India)

### Database errors
- Delete `tailor_pro.db` to reset database
- Check file permissions in project directory

## Future Enhancements
- User authentication and roles
- Multi-user support
- Payment integration
- Email notifications
- Advanced reporting
- Mobile app
- Backup and restore
- Bulk import/export

## Support & Contributions
For issues or suggestions, please refer to the application logs.

## License
Created for small tailor shops and tailoring businesses.

---

**Version**: 1.0  
**Last Updated**: February 2026
