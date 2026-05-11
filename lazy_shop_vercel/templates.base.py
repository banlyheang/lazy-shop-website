from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os
import json
import uuid
import qrcode
from io import BytesIO
import base64
import random
from supabase import create_client, Client

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SESSION_TYPE'] = 'filesystem'

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

STORE_NAME = "L@ZY SHOP"
CONTACT_PHONE = "0969903084"
CONTACT_TELEGRAM = "https://t.me/lixing26"
MANUAL_PAYMENT_BANK_NAME = "ABA Bank"
MANUAL_PAYMENT_ACCOUNT_NAME = "Ban Lyheang"
MANUAL_PAYMENT_ACCOUNT_NUMBER = "001059172"

Session(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login first!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login first!', 'danger')
            return redirect(url_for('login'))
        user = supabase.table('users').select('is_admin').eq('id', session['user_id']).execute()
        if not user.data or not user.data[0].get('is_admin'):
            flash('Admin access required!', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def get_cart_count():
    if not session.get('user_id'):
        return 0
    cart = supabase.table('cart').select('*', count='exact').eq('user_id', session['user_id']).execute()
    return cart.count if cart.count else 0

def generate_order_number():
    now = datetime.now()
    return f"ORD{now.strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"

@app.route('/')
def index():
    featured = supabase.table('products').select('*').eq('is_active', True).limit(8).execute()
    return render_template('index.html', featured_products=featured.data, cart_count=get_cart_count())

@app.route('/shop')
def shop():
    products = supabase.table('products').select('*').eq('is_active', True).execute()
    return render_template('shop.html', products=products.data, cart_count=get_cart_count())

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = supabase.table('products').select('*').eq('id', product_id).execute()
    if not product.data:
        flash('Product not found!', 'danger')
        return redirect(url_for('shop'))
    return render_template('product.html', product=product.data[0], cart_count=get_cart_count())

@app.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    
    existing = supabase.table('cart').select('*').eq('user_id', session['user_id']).eq('product_id', product_id).execute()
    
    if existing.data:
        supabase.table('cart').update({'quantity': existing.data[0]['quantity'] + quantity}).eq('id', existing.data[0]['id']).execute()
    else:
        supabase.table('cart').insert({'user_id': session['user_id'], 'product_id': product_id, 'quantity': quantity}).execute()
    
    flash('Added to cart!', 'success')
    return redirect(request.referrer)

@app.route('/cart')
@login_required
def cart():
    items = supabase.table('cart').select('*, products(*)').eq('user_id', session['user_id']).execute()
    total = sum(item['products']['price'] * item['quantity'] for item in items.data if item.get('products'))
    return render_template('cart.html', cart_items=items.data, total=total, cart_count=get_cart_count())

@app.route('/update-cart', methods=['POST'])
@login_required
def update_cart():
    item_id = request.form.get('item_id', type=int)
    quantity = request.form.get('quantity', type=int)
    
    if quantity <= 0:
        supabase.table('cart').delete().eq('id', item_id).execute()
    else:
        supabase.table('cart').update({'quantity': quantity}).eq('id', item_id).execute()
    
    flash('Cart updated!', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items = supabase.table('cart').select('*, products(*)').eq('user_id', session['user_id']).execute()
    
    if not items.data:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('shop'))
    
    total = sum(item['products']['price'] * item['quantity'] for item in items.data)
    
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        customer_phone = request.form.get('customer_phone')
        delivery_address = request.form.get('delivery_address')
        
        order_number = generate_order_number()
        order_items = json.dumps([{
            'product_id': item['product_id'],
            'product_name': item['products']['name'],
            'price': item['products']['price'],
            'quantity': item['quantity']
        } for item in items.data])
        
        order_data = {
            'order_number': order_number,
            'user_id': session['user_id'],
            'total_amount': total,
            'customer_name': customer_name,
            'customer_phone': customer_phone,
            'delivery_address': delivery_address,
            'order_items_json': order_items,
            'payment_status': 'pending',
            'order_status': 'pending'
        }
        
        result = supabase.table('orders').insert(order_data).execute()
        
        supabase.table('cart').delete().eq('user_id', session['user_id']).execute()
        
        flash(f'Order #{order_number} created!', 'success')
        return redirect(url_for('order_payment', order_id=result.data[0]['id']))
    
    return render_template('checkout.html', cart_items=items.data, total=total, cart_count=get_cart_count())

@app.route('/order-payment/<int:order_id>')
@login_required
def order_payment(order_id):
    order = supabase.table('orders').select('*').eq('id', order_id).eq('user_id', session['user_id']).execute()
    
    if not order.data:
        flash('Order not found!', 'danger')
        return redirect(url_for('orders'))
    
    order = order.data[0]
    
    qr_data = f"Bank: {MANUAL_PAYMENT_BANK_NAME}\nAccount: {MANUAL_PAYMENT_ACCOUNT_NUMBER}\nName: {MANUAL_PAYMENT_ACCOUNT_NAME}\nAmount: ${order['total_amount']:.2f}"
    
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    qr_buffer = BytesIO()
    img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()
    
    return render_template('payment.html', order=order, qr_base64=qr_base64, cart_count=get_cart_count())

@app.route('/orders')
@login_required
def orders():
    user_orders = supabase.table('orders').select('*').eq('user_id', session['user_id']).order('created_at', desc=True).execute()
    return render_template('orders.html', orders=user_orders.data, cart_count=get_cart_count())

@app.route('/order-tracking/<int:order_id>')
@login_required
def order_tracking(order_id):
    order = supabase.table('orders').select('*').eq('id', order_id).execute()
    if not order.data or order.data[0]['user_id'] != session['user_id']:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('orders'))
    return render_template('order_tracking.html', order=order.data[0], cart_count=get_cart_count())

@app.route('/contact')
def contact():
    return render_template('contact.html', phone=CONTACT_PHONE, telegram=CONTACT_TELEGRAM, cart_count=get_cart_count())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = supabase.table('users').select('*').eq('username', username).execute()
        
        if user.data and check_password_hash(user.data[0]['password_hash'], password):
            session['user_id'] = user.data[0]['id']
            session['username'] = user.data[0]['username']
            session['is_admin'] = user.data[0].get('is_admin', False)
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html', cart_count=get_cart_count())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
        
        existing = supabase.table('users').select('*').eq('username', username).execute()
        if existing.data:
            flash('Username already exists!', 'danger')
            return render_template('register.html')
        
        user_data = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'is_admin': False
        }
        
        result = supabase.table('users').insert(user_data).execute()
        
        if result.data:
            session['user_id'] = result.data[0]['id']
            session['username'] = username
            flash('Registration successful!', 'success')
            return redirect(url_for('index'))
    
    return render_template('register.html', cart_count=get_cart_count())

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out!', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    users = supabase.table('users').select('*', count='exact').execute()
    orders = supabase.table('orders').select('*', count='exact').execute()
    stats = {'total_users': users.count, 'total_orders': orders.count}
    return render_template('admin.html', stats=stats, cart_count=get_cart_count())

@app.route('/api/cart/count')
@login_required
def api_cart_count():
    return jsonify({'count': get_cart_count()})

if __name__ == '__main__':
    app.run(debug=True)