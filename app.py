from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# SQLiteデータベースへの接続
def get_db_connection():
    conn = sqlite3.connect('cafe_management.db')
    conn.row_factory = sqlite3.Row
    return conn

# 商品入力ページの表示
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        stock = request.form['stock']
        price = request.form['price']

        conn = get_db_connection()
        conn.execute('INSERT INTO Product (Name, Category, Stock, Price) VALUES (?, ?, ?, ?)',
                     (name, category, stock, price))
        conn.commit()
        conn.close()
        
        return redirect(url_for('add_product'))

    return render_template('add_product.html')

# 商品一覧ページの表示
@app.route('/products')
def show_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM Product').fetchall()
    conn.close()
    return render_template('product_list.html', products=products)

if __name__ == '__main__':
    app.run(debug=True)
