from flask import Flask, render_template, request, redirect, url_for, flash
import db
import reports
import traceback
import logging
from logging.handlers import RotatingFileHandler
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Needed for flash messages

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Application startup')

# ----------------- Error Handlers -----------------
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'404 Error: {error}')
    return render_template('error.html', error_message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'500 Error: {error}')
    return render_template('error.html', error_message='Internal server error'), 500

@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.error(f'Unhandled Exception: {error}')
    return render_template('error.html', error_message='An unexpected error occurred'), 500

# ----------------- Home / Dashboard -----------------
@app.route("/")
def index():
    try:
        app.logger.info('Dashboard accessed')
        return render_template("index.html", title="Dashboard")
    except Exception as e:
        app.logger.error(f'Error in index route: {traceback.format_exc()}')
        flash('Error loading dashboard', 'error')
        return render_template("index.html", title="Dashboard")

# ----------------- Products -----------------
@app.route("/products", methods=["GET", "POST"])
def products_page():
    try:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            price_str = request.form.get("price", "0")
            stock_str = request.form.get("stock", "0")
            
            # Validate inputs
            if not name:
                flash('Product name is required', 'error')
                return redirect(url_for("products_page"))
            
            try:
                price = float(price_str)
                stock = int(stock_str)
                
                if price <= 0:
                    flash('Price must be greater than 0', 'error')
                    return redirect(url_for("products_page"))
                
                if stock < 0:
                    flash('Stock cannot be negative', 'error')
                    return redirect(url_for("products_page"))
                    
            except ValueError:
                flash('Invalid price or stock value', 'error')
                return redirect(url_for("products_page"))
            
            db.add_product(name, price, stock)
            flash('Product added successfully!', 'success')
            app.logger.info(f'Product added: {name}')
            return redirect(url_for("products_page"))

        products = db.get_products()
        return render_template("products.html", title="Products", products=products)
    
    except Exception as e:
        app.logger.error(f'Error in products_page route: {traceback.format_exc()}')
        flash('Error loading products page', 'error')
        return redirect(url_for("index"))

# ----------------- Customers -----------------
@app.route("/customers", methods=["GET", "POST"])
def customers_page():
    try:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            contact = request.form.get("contact", "").strip()
            address = request.form.get("address", "").strip()
            
            # Validate inputs
            if not name:
                flash('Customer name is required', 'error')
                return redirect(url_for("customers_page"))
                
            if not contact:
                flash('Contact information is required', 'error')
                return redirect(url_for("customers_page"))
            
            db.add_customer(name, contact, address)
            flash('Customer added successfully!', 'success')
            app.logger.info(f'Customer added: {name}')
            return redirect(url_for("customers_page"))

        customers = db.get_customers()
        return render_template("customers.html", title="Customers", customers=customers)
    
    except Exception as e:
        app.logger.error(f'Error in customers_page route: {traceback.format_exc()}')
        flash('Error loading customers page', 'error')
        return redirect(url_for("index"))

# ----------------- Billing -----------------
@app.route("/billing", methods=["GET", "POST"])
def billing_page():
    try:
        if request.method == "POST":
            customer_id_str = request.form.get("customer_id", "")
            
            if not customer_id_str:
                flash('Please select a customer', 'error')
                return redirect(url_for("billing_page"))
                
            try:
                customer_id = int(customer_id_str)
            except ValueError:
                flash('Invalid customer selection', 'error')
                return redirect(url_for("billing_page"))
            
            items = []
            products = db.get_products()
            has_items = False
            
            for p in products:
                qty_str = request.form.get(f"qty_{p['id']}", "0")
                try:
                    qty = int(qty_str)
                    if qty > 0:
                        if qty > p['stock']:
                            flash(f'Not enough stock for {p["name"]}. Only {p["stock"]} available.', 'error')
                            return redirect(url_for("billing_page"))
                            
                        items.append({
                            "id": p["id"], 
                            "name": p["name"], 
                            "price": p["price"], 
                            "qty": qty
                        })
                        has_items = True
                except ValueError:
                    flash(f'Invalid quantity for {p["name"]}', 'error')
                    return redirect(url_for("billing_page"))
            
            if not has_items:
                flash('Please select at least one product', 'error')
                return redirect(url_for("billing_page"))

            invoice_id, grand_total = db.create_invoice(customer_id, items)
            flash('Invoice created successfully!', 'success')
            app.logger.info(f'Invoice created: {invoice_id}')
            return redirect(url_for("invoice_page", invoice_id=invoice_id))

        products = db.get_products()
        customers = db.get_customers()
        
        if not products:
            flash('No products available. Please add products first.', 'warning')
            
        if not customers:
            flash('No customers available. Please add customers first.', 'warning')
            
        return render_template("billing.html", title="Billing", products=products, customers=customers)
    
    except Exception as e:
        app.logger.error(f'Error in billing_page route: {traceback.format_exc()}')
        flash('Error processing billing request', 'error')
        return redirect(url_for("billing_page"))

# ----------------- Invoice -----------------
@app.route("/invoice/<int:invoice_id>")
def invoice_page(invoice_id):
    try:
        invoice = db.get_invoice(invoice_id)
        if not invoice:
            flash('Invoice not found', 'error')
            app.logger.error(f'Invoice not found: {invoice_id}')
            return redirect(url_for("billing_page"))
            
        customer = db.get_customer(invoice["customer_id"])
        if not customer:
            flash('Customer not found for this invoice', 'error')
            app.logger.error(f'Customer not found for invoice: {invoice_id}')
            return redirect(url_for("billing_page"))
            
        items = db.get_invoice_items(invoice_id)
        if not items:
            flash('No items found for this invoice', 'error')
            app.logger.error(f'No items found for invoice: {invoice_id}')
            return redirect(url_for("billing_page"))
            
        grand_total = sum(i["price"] * i["qty"] for i in items)
        
        app.logger.info(f'Invoice viewed: {invoice_id}')
        return render_template(
            "invoice.html", 
            title="Invoice", 
            customer=customer, 
            items=items, 
            grand_total=grand_total,
            invoice_id=invoice_id
        )
    
    except Exception as e:
        app.logger.error(f'Error in invoice_page route: {traceback.format_exc()}')
        flash('Error loading invoice', 'error')
        return redirect(url_for("billing_page"))

# ----------------- Reports -----------------
@app.route("/reports")
def reports_page():
    try:
        revenue = reports.get_revenue()
        sales = reports.get_sales_report()
        stock = reports.get_stock_report()
        
        app.logger.info('Reports page accessed')
        return render_template(
            "reports.html", 
            title="Reports", 
            revenue=revenue, 
            sales=sales, 
            stock=stock
        )
    
    except Exception as e:
        app.logger.error(f'Error in reports_page route: {traceback.format_exc()}')
        flash('Error generating reports', 'error')
        return redirect(url_for("index"))

# ----------------- Health Check -----------------
@app.route("/health")
def health_check():
    try:
        # Test database connection
        db.get_connection().close()
        return "OK", 200
    except Exception as e:
        app.logger.error(f'Health check failed: {e}')
        return "Database connection failed", 500

if __name__ == "__main__":
    try:
        db.init_db()
        app.logger.info('Database initialized successfully')
        print("Database initialized successfully")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        app.logger.error(f'Failed to initialize application: {traceback.format_exc()}')
        print(f"Failed to initialize application: {e}")