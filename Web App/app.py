from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import pymysql
import bcrypt
import os
import pandas as pd
from functools import wraps  # Import wraps
from bank_statement_extraction.app_bbva_debito import process_pdf_bbva_debito
from bank_statement_extraction.app_bbva_credito import process_pdf_bbva_credito
from bank_statement_extraction.app_santander_debito import process_pdf_santander_debito
from app_eda import perform_eda
from app_expenses_analysis import analyze_expenses
from app_interactive_visuals import plot_income_expenses_line, plot_income_expenses_pie
from app_personalized_recommendations import calculate_financial_recommendations

app = Flask(__name__)
app.secret_key = 'your_very_secret_key'

# Set the base directory to the directory where app.py is located
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'UPLOAD_FOLDER')


# MySQL configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'boliviano314',
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
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    # Default values for variables
    fondo_emergencia = 0
    excedente_invertir = 0

    cnx = get_db_connection()
    query = f'''
    SELECT `Date`, `Description`, `Debit`, `Credit`, `Amount`, `Category_type`, `Category`
    FROM transactions
    WHERE user_id = {user_id};
    '''
    df = pd.read_sql(query, cnx, parse_dates=['Date'])
    cnx.close()
    if df.empty:
        return render_template('dashboard.html',
                               message="There is no data for this user",
                               fondo_emergencia=fondo_emergencia,
                               excedente_invertir=excedente_invertir)
    # Perform EDA
    plot_data = perform_eda(df)

    # Perform expense analysis
    expense_plot_url = analyze_expenses(df)

    ######

    cnx = get_db_connection()
    query = f'''
        SELECT `Date`, `Description`, `Debit`, `Credit`, `Amount`, `Category_type`, `Category`
        FROM transactions
        WHERE user_id = {user_id};
        '''
    df1 = pd.read_sql(query, cnx, parse_dates=['Date'])
    cnx.close()
    if df.empty:
        return render_template('dashboard.html',
                               message="There is no data for this user",
                               fondo_emergencia=fondo_emergencia,
                               excedente_invertir=excedente_invertir)



    line_plot_html = plot_income_expenses_line(df1)
    pie_plot_html = plot_income_expenses_pie(df1)

    # Call the function with the user's DataFrame
    gastos_mensuales, expenses_by_category, fondo_emergencia, excedente_invertir = calculate_financial_recommendations(
        df1)

    # Convert the DataFrames to HTML to render as tables in the dashboard
    gastos_mensuales_df = gastos_mensuales.to_frame() if isinstance(gastos_mensuales, pd.Series) else gastos_mensuales

    # Now you can use to_html() on the DataFrame
    gastos_mensuales_html = gastos_mensuales_df.to_html()
    expenses_by_category_html = expenses_by_category.to_html()

    #####

    # Pass all plot data to the template
    return render_template('dashboard.html',
                           monthly_income_expenses=plot_data['monthly_income_expenses'],
                           expense_distribution=plot_data['expense_distribution'],
                           expense_plot_url=expense_plot_url,
                           line_plot_html=line_plot_html,
                           pie_plot_html=pie_plot_html,
                           gastos_mensuales=gastos_mensuales_html,
                           expenses_by_category=expenses_by_category_html,
                           fondo_emergencia=fondo_emergencia,
                           excedente_invertir=excedente_invertir
                           )

@app.route('/transactions')
@login_required
def transactions():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    cnx = get_db_connection()
    df = pd.read_sql(
        "SELECT `Date`, `Description`, `Debit`, `Credit`, `Amount`, `Category_type`, `Category` FROM transactions WHERE user_id = {};".format(
            user_id), cnx, parse_dates=['Date'])
    cnx.close()
    if df.empty:
        return render_template('transactions.html', message="There is no data for this user")
    # Generate a list of unique months in the 'YYYY-MM' format
    df['Month'] = df['Date'].dt.strftime('%Y-%m')
    months_list = df['Month'].unique().tolist()

    # Render the transactions template with all the data
    return render_template('transactions.html', months=months_list)



@app.route('/get_gastos_mensuales/<string:month>', methods=['GET'])
def get_gastos_mensuales(month):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    cnx = get_db_connection()
    df = pd.read_sql("SELECT `Date`, `Description`, `Debit`, `Credit`, `Amount`, `Category_type`, `Category` FROM transactions WHERE user_id = {};".format(user_id), cnx, parse_dates=['Date'])
    cnx.close()
    if df.empty:
        return "There is no data for this user", 200
    # Ensure df['Date'] is converted to a period
    df['Month'] = df['Date'].dt.strftime('%Y-%m')

    try:
        # Convert month parameter to period type before filtering
        month_period = pd.Period(month, freq='M')
    except Exception as e:
        # Log the error and perhaps return a user-friendly message or redirect
        print("Error parsing the month: ", e)
        return "Error parsing the selected month.", 400  # Or handle as appropriate

    # Filter data for the selected month and format it to HTML
    gastos_mensuales_filtered = df[df['Month'] == month]  # Compare with the string formatted month

    return gastos_mensuales_filtered.to_html(classes='table table-responsive')







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


@app.route('/upload_bank_statement', methods=['GET'])
@login_required
def upload_bank_statement():
    return render_template('upload_bank_statement.html')


@app.route('/handle_bank_statement', methods=['POST'])
@login_required
def handle_bank_statement():
    if 'bank_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['bank_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Retrieve selected bank from the form
        bank_name = request.form.get('bank_name')
        conn = get_db_connection()
        try:
            if bank_name == 'bbva_debito':
                process_pdf_bbva_debito(file_path, session['user_id'], conn)
            elif bank_name == 'bbva_credito':
                process_pdf_bbva_credito(file_path, session['user_id'], conn)
            elif bank_name == 'santander_debito':
                process_pdf_santander_debito(file_path, session['user_id'], conn)
            flash('File processed successfully')
        except Exception as e:
            flash(f'Error processing file: {e}')
        finally:
            conn.close()

        return redirect(url_for('upload_bank_statement'))
    else:
        flash('Allowed file types are PDFs')
        return redirect(url_for('upload_bank_statement'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf']


if __name__ == '__main__':
    app.run(debug=True)
