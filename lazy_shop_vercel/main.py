from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os
import json
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

Session(app)

def get_cart_count():
    if not session.get('user_id'):
        return 0
    cart = supabase.table('cart').select('*', count='exact').eq('user_id', session['user_id']).execute()
    return cart.count if cart.count else 0

@app.route('/')
def index():
    return render_template('index.html', cart_count=get_cart_count())

@app.route('/shop')
def shop():
    products = supabase.table('products').select('*').eq('is_active', True).execute()
    return render_template('shop.html', products=products.data, cart_count=get_cart_count())

@app.route('/cart')
def cart():
    return render_template('cart.html', cart_count=get_cart_count())

@app.route('/login', methods=['GET', 'POST'])
def login():
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

@app.route('/contact')
def contact():
    return render_template('contact.html', phone="0969903084", cart_count=get_cart_count())

if __name__ == '__main__':
    app.run(debug=True)
