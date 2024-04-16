from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
import bcrypt
from functools import wraps  # Import wraps

app = Flask(__name__)
app.secret_key = 'your_very_secret_key'

# MySQL configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'finanzas_personales',
}

# Decorator to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to view this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Function to get database connection
def get_db_connection():
    return pymysql.connect(**db_config)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                result = cur.execute('SELECT * FROM users WHERE username = %s', [username])
                if result > 0:
                    user_data = cur.fetchone()
                    if bcrypt.checkpw(password, user_data[3].encode('utf-8')):
                        session['user_id'] = user_data[0]  # Save the user's id to the session
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Invalid Login credentials!')
                else:
                    flash('Username not found!')
        except Exception as e:
            print("Database connection problem:", e)
            flash('A database error occurred. Please try again.')
        finally:
            conn.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("INSERT INTO users(username, email, password_hash) VALUES(%s, %s, %s)",
                            (username, email, hashed_password.decode('utf-8')))
            conn.commit()
            flash('You are now registered and can log in', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print("Database connection problem:", e)
            flash('A database error occurred. Please try again.')
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/upload_transactions', methods=['GET'])
@login_required
def upload_transactions():
    return render_template('upload_transactions.html')

@app.route('/handle_transaction', methods=['POST'])
@login_required
def handle_transaction():
    # Retrieve form data
    category_type = request.form.get('category_type')
    date = request.form.get('date')
    description = request.form.get('description')
    amount = float(request.form.get('amount'))
    category = request.form.get('category')

    debit = 0
    credit = 0

    if category_type == 'income':
        credit = amount
    elif category_type == 'expenses':
        debit = amount
        amount = -amount  # Store amount as negative for expenses

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            user_id = session.get('user_id')  # Get user_id from the session
            sql = """
            INSERT INTO transactions (user_id, date, description, debit, credit, amount, category_type, category) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, date, description, debit, credit, amount, category_type, category))
        conn.commit()
        flash('Transaction uploaded successfully!')
    except Exception as e:
        print("Database error:", e)
        flash('An error occurred. Please try again.')
        conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('upload_transactions'))

if __name__ == '__main__':
    app.run(debug=True)

