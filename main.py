import pandas as pd
import pymysql
from eda import perform_eda  # Make sure eda.py is in the same directory as this file
from transaction_classification import classify_transactions
from expenses_analysis import analyze_expenses
from predictions import simulate_savings

def fetch_data(user_id):
    # Database connection values
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'boliviano314',
        'database': 'finanzas_personales'
    }

    # Establish a database connection using pymysql
    cnx = pymysql.connect(**db_config)

    # SQL Query
    query = f'''
    SELECT `Date`, `Description`, `Debit`, `Credit`, `Amount`, `Category_type`, `Category`
    FROM transactions
    WHERE user_id = {user_id};
    '''

    # Load the data into a pandas DataFrame
    df = pd.read_sql(query, cnx, parse_dates=['Date'])

    # Close the database connection
    cnx.close()

    return df

if __name__ == "__main__":
    user_id = 1  # Or parse this from command-line arguments/sys.argv if you prefer
    df_transactions = fetch_data(user_id)
    # perform_eda(df_transactions)
    # model, vectorizer, percent_spent = classify_transactions(df_transactions)
    # forecast, gastos_ordenados = analyze_expenses(df_transactions)
    summary_statistics = simulate_savings(df_transactions)
    print(summary_statistics)

#