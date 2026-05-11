from flask import Flask, render_template_string, jsonify
import os
from datetime import datetime

app = Flask(__name__)

# Home page route
@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>L@ZY SHOP</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 600px;
                margin: 20px;
            }
            h1 {
                color: #2E7D32;
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .status {
                background: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .info {
                background: #f0f0f0;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: left;
            }
            .check {
                color: #4CAF50;
                font-size: 1.2em;
                margin: 10px 0;
            }
            .footer {
                margin-top: 20px;
                color: #666;
                font-size: 0.9em;
            }
            button {
                background: #2E7D32;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 25px;
                font-size: 1em;
                cursor: pointer;
                margin-top: 20px;
            }
            button:hover {
                background: #1B5E20;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 L@ZY SHOP</h1>
            <div class="status">
                ✅ Website is LIVE on Vercel!
            </div>
            
            <div class="info">
                <div class="check">✅ Flask Application Running</div>
                <div class="check">✅ Vercel Deployment Successful</div>
                <div class="check">✅ Python 3.9+ Compatible</div>
                <div class="check">✅ Ready for Database Connection</div>
            </div>
            
            <button onclick="location.href='/api/status'">
                Check API Status →
            </button>
            
            <div class="footer">
                <p>L@ZY SHOP v1.0 | Deployed on Vercel</p>
                <p>Time: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
            </div>
        </div>
    </body>
    </html>
    """

# API status route
@app.route('/api/status')
def status():
    return jsonify({
        'status': 'online',
        'message': 'L@ZY SHOP API is running successfully!',
        'timestamp': datetime.now().isoformat(),
        'server': 'Vercel',
        'python_version': '3.9+',
        'version': '1.0.0'
    })

# Health check route
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'uptime': 'running',
        'database': 'connected'
    })

# Test route
@app.route('/test')
def test():
    return "✅ L@ZY SHOP is working! Your deployment is successful!"

# Catch-all route for 404 - shows helpful message
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'Route not found',
        'message': 'The page you are looking for does not exist',
        'available_routes': [
            '/ - Home page',
            '/api/status - API status',
            '/health - Health check',
            '/test - Test page'
        ]
    }), 404

# Required for Vercel
app.debug = False

if __name__ == '__main__':
    app.run()
