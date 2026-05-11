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

@app.route('/login')
def login():
    return render_template('login.html', cart_count=get_cart_count())

@app.route('/register')
def register():
    return render_template('register.html', cart_count=get_cart_count())

@app.route('/contact')
def contact():
    return render_template('contact.html', cart_count=get_cart_count())

if __name__ == '__main__':
    app.run(debug=True)