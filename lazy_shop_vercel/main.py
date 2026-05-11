from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "L@ZY SHOP is WORKING! 🚀 - Version 2"

@app.route('/shop')
def shop():
    return "Shop Page"

if __name__ == '__main__':
    app.run()
