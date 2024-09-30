from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

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

# 入出庫機能の追加
# 商品入出庫ページの表示および処理
@app.route('/transaction', methods=['GET', 'POST'])
def manage_transaction():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM Product').fetchall()
    conn.close()
    
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])
        memo = request.form['memo']
        transaction_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # StockTransactionテーブルにレコードを追加
        conn = get_db_connection()
        conn.execute('INSERT INTO `StockTransaction` (ProductID, UserID, Quantity, Date, Memo) VALUES (?, ?, ?, ?, ?)',
                     (product_id, 1, quantity, transaction_date, memo))  # ユーザーIDは仮で1にしています
        conn.commit()
        
        # 商品在庫の更新
        conn.execute('UPDATE Product SET Stock = Stock + ? WHERE ID = ?',
                     (quantity, product_id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('show_transactions'))

    return render_template('transaction.html', products=products)

# 入出庫履歴ページの表示
@app.route('/transactions')
def show_transactions():
    conn = get_db_connection()
    transactions = conn.execute('''
        SELECT StockTransaction.ID, Product.Name, StockTransaction.Quantity, StockTransaction.Date, StockTransaction.Memo
        FROM StockTransaction
        JOIN Product ON StockTransaction.ProductID = Product.ID
    ''').fetchall()
    conn.close()
    
    return render_template('transaction_list.html', transactions=transactions)



if __name__ == '__main__':
    app.run(debug=True)
