# SETUP GUIDE - TailorPro Application

## Quick Start (3 Minutes)

### For Windows Users:

1. **Double-click `start.bat`** in the project folder
   - This will automatically set up everything and start the app
   - Your browser should open at `http://127.0.0.1:5000`

2. **If browser doesn't open automatically**, open it manually:
   - Go to: `http://127.0.0.1:5000`
   - You should see the TailorPro Dashboard

3. **To stop the application**: Press `Ctrl+C` in the terminal window

---

### For Mac/Linux Users:

1. **Open Terminal** and navigate to the project folder:
   ```bash
   cd /path/to/tailor_app
   ```

2. **Run the startup script**:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
   Or directly:
   ```bash
   python app.py
   ```

3. **Open your browser** and go to:
   ```
   http://127.0.0.1:5000
   ```

---

## Manual Setup (If Automatic Setup Fails)

### Step 1: Install Python
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **Mac**: Use Homebrew: `brew install python3`
- **Linux**: `sudo apt-get install python3 python3-pip`

### Step 2: Create Virtual Environment
```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment

**Windows**:
```bash
venv\Scripts\activate
```

**Mac/Linux**:
```bash
source venv/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Run the Application
```bash
python app.py
```

---

## First Time Setup Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] No errors when starting app
- [ ] Can access `http://127.0.0.1:5000` in browser
- [ ] Database created (will be at `tailor_pro.db`)

---

## Getting Started with the App

### 1. Add Your First Customer
- Click "Customers" in the top menu
- Click "+ Add Customer"
- Fill in: Name, Phone, Address
- Click "Save Customer"

### 2. Create an Order
- Click "Dashboard" or "+ New Order"
- Select customer from dropdown
- Enter garment type: "Shirt", "Pant", "Saree", etc.
- Select due date
- Enter measurements: Length, Chest, Shoulder
- Enter bill amount
- Click "Confirm Order"

### 3. View & Manage Orders
- Click "Orders" in the menu
- See all pending orders
- Click "Edit" to change status
- Click "Bill" to view/print invoice
- Click WhatsApp icon to send reminder

### 4. Track Inventory
- Click "Inventory" in menu
- Click "+ Add Item" to add materials
- Track stock levels
- Get low stock warnings

---

## Keyboard Shortcuts

- `Ctrl+C` - Stop the application
- `Ctrl+R` - Refresh the page
- `Ctrl+P` - Print billing page

---

## Troubleshooting

### Problem: "Port 5000 already in use"
**Solution**: 
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (Windows)
taskkill /PID <PID> /F

# Try again
python app.py
```

### Problem: "Module not found" error
**Solution**: Make sure you're in the virtual environment
```bash
# Windows
venv\Scripts\activate

# Mac/Linux  
source venv/bin/activate

# Then install again
pip install -r requirements.txt
```

### Problem: Database error
**Solution**: Delete `tailor_pro.db` file - it will be recreated automatically

### Problem: WhatsApp not working
**Solution**: WhatsApp feature requires internet. Make sure:
- Internet connection is active
- Phone number format: 10 digits (without country code) or with +91
- Browser allows access to system

---

## Database Location

The SQLite database is stored at:
```
d:\Backup\Tailor_app\tailor_pro.db
```

**To backup your data**: Simply copy the `tailor_pro.db` file to a safe location.

---

## File Structure

```
tailor_app/
├── app.py                    # Main application
├── requirements.txt          # Python packages
├── tailor_pro.db            # Database (auto-created)
├── start.bat                # Quick start for Windows
├── start.sh                 # Quick start for Mac/Linux
├── run.py                   # Alternative way to run
├── README.md                # Full documentation
├── SETUP.md                 # This file
├── static/
│   └── css/
│       └── style.css        # Application styling
└── templates/               # HTML pages
    ├── layout.html
    ├── index.html
    ├── customers.html
    ├── orders_list.html
    └── ... (other pages)
```

---

## Default Settings

- **Server**: http://127.0.0.1
- **Port**: 5000
- **Database**: SQLite (tailor_pro.db)
- **Debug Mode**: Enabled (auto-reload on changes)

---

## Disabling Debug Mode (For Production)

Edit `app.py`, change the last line:

```python
# Current (debug enabled)
app.run(debug=True, host='127.0.0.1', port=5000)

# Production (debug disabled)
app.run(debug=False, host='0.0.0.0', port=5000)
```

---

## Next Steps

1. ✅ Get the app running
2. 📱 Add some sample customers
3. 📋 Create test orders
4. 🧾 Generate a bill
5. 📦 Add inventory items

---

## Need Help?

- Check the README.md file for complete documentation
- Look at the app structure - everything is well-commented
- Database tables are auto-created on first run

**Happy tailoring! 🧵✂️**
