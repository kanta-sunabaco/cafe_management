from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッションのための秘密鍵

# SQLiteデータベースへの接続
def get_db_connection():
    conn = sqlite3.connect('cafe_management.db')
    conn.row_factory = sqlite3.Row
    return conn

# ログインページの表示および処理
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM User WHERE Name = ?', (name,)).fetchone()
        conn.close()

        if user and check_password_hash(user['Password'], password):
            session['user_id'] = user['ID']
            session['user_name'] = user['DisplayName']
            session['user_role'] = user['Role']
            flash('ログインに成功しました！', 'success')
            return redirect(url_for('show_products'))
        else:
            flash('ユーザー名またはパスワードが間違っています。', 'danger')

    return render_template('login.html')

# ログアウト機能
@app.route('/logout')
def logout():
    session.clear()
    flash('ログアウトしました。', 'success')
    return redirect(url_for('login'))

# 商品入力ページの表示および処理
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        flash('ログインしてください。', 'warning')
        return redirect(url_for('login'))

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

# 商品編集ページの表示および処理
@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'user_id' not in session:
        flash('ログインしてください。', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM Product WHERE ID = ?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        stock = request.form['stock']
        price = request.form['price']

        conn.execute('UPDATE Product SET Name = ?, Category = ?, Stock = ?, Price = ? WHERE ID = ?',
                     (name, category, stock, price, id))
        conn.commit()
        conn.close()

        return redirect(url_for('show_products'))

    conn.close()
    return render_template('edit_product.html', product=product)

# 商品削除機能
@app.route('/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    if 'user_id' not in session:
        flash('ログインしてください。', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM Product WHERE ID = ?', (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('show_products'))

# 商品一覧ページの表示
@app.route('/products')
def show_products():
    if 'user_id' not in session:
        flash('ログインしてください。', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    products = conn.execute('SELECT * FROM Product').fetchall()
    conn.close()
    return render_template('product_list.html', products=products)

# 入出庫機能の追加
@app.route('/transaction', methods=['GET', 'POST'])
def manage_transaction():
    if 'user_id' not in session:
        flash('ログインしてください。', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    products = conn.execute('SELECT * FROM Product').fetchall()
    conn.close()

    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])
        memo = request.form['memo']
        transaction_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        conn.execute('INSERT INTO StockTransaction (ProductID, UserID, Quantity, Date, Memo) VALUES (?, ?, ?, ?, ?)',
                     (product_id, session['user_id'], quantity, transaction_date, memo))
        conn.commit()

        conn.execute('UPDATE Product SET Stock = Stock + ? WHERE ID = ?', (quantity, product_id))
        conn.commit()
        conn.close()

        return redirect(url_for('show_transactions'))

    return render_template('transaction.html', products=products)

# 入出庫履歴ページの表示
@app.route('/transactions')
def show_transactions():
    if 'user_id' not in session:
        flash('ログインしてください。', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    transactions = conn.execute('''
        SELECT StockTransaction.ID, Product.Name, StockTransaction.Quantity, StockTransaction.Date, StockTransaction.Memo
        FROM StockTransaction
        JOIN Product ON StockTransaction.ProductID = Product.ID
    ''').fetchall()
    conn.close()

    return render_template('transaction_list.html', transactions=transactions)

# 入出庫履歴編集ページの表示および処理
@app.route('/edit_transaction/<int:id>', methods=['GET', 'POST'])
def edit_transaction(id):
    if 'user_id' not in session:
        flash('ログインしてください。', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    transaction = conn.execute('SELECT * FROM StockTransaction WHERE ID = ?', (id,)).fetchone()
    products = conn.execute('SELECT * FROM Product').fetchall()

    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])
        memo = request.form['memo']

        conn.execute('UPDATE StockTransaction SET ProductID = ?, Quantity = ?, Memo = ? WHERE ID = ?',
                     (product_id, quantity, memo, id))
        conn.commit()

        # 在庫数を更新（過去の数量との差分を反映）
        old_quantity = transaction['Quantity']
        quantity_diff = quantity - old_quantity
        conn.execute('UPDATE Product SET Stock = Stock + ? WHERE ID = ?', (quantity_diff, product_id))
        conn.commit()

        conn.close()

        return redirect(url_for('show_transactions'))

    conn.close()
    return render_template('edit_transaction.html', transaction=transaction, products=products)

# 入出庫履歴削除機能
@app.route('/delete_transaction/<int:id>', methods=['POST'])
def delete_transaction(id):
    if 'user_id' not in session:
        flash('ログインしてください。', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    transaction = conn.execute('SELECT * FROM StockTransaction WHERE ID = ?', (id,)).fetchone()

    conn.execute('UPDATE Product SET Stock = Stock - ? WHERE ID = ?', (transaction['Quantity'], transaction['ProductID']))
    conn.commit()

    conn.execute('DELETE FROM StockTransaction WHERE ID = ?', (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('show_transactions'))

# ユーザー登録ページの表示および処理
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        role = request.form['role']
        display_name = request.form['display_name']

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        conn.execute('INSERT INTO User (Name, Password, Role, DisplayName) VALUES (?, ?, ?, ?)',
                     (name, hashed_password, role, display_name))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
