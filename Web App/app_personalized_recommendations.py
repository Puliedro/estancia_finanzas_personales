import pandas as pd


def calculate_financial_recommendations(df):
    # Assume 'df' has columns 'Date', 'Category_type
    # ', 'Category', 'Amount'

    # Group expenses by month and category
    gastos_mensuales = df[df['Category_type' \
                             ''] == 'expenses'].groupby([df['Date'].dt.to_period('M'), 'Category'])[
        'Amount'].sum()

    # Summarize expenses by category
    expenses_by_category = df[df['Category_type' \
                                 ''] == 'expenses'].groupby('Category')['Amount'].sum().sort_values(
        ascending=False).reset_index()

    # Calculate standard deviation of expenses and suggest emergency fund
    std_gastos = df[df['Category_type' \
                       ''] == 'expenses']['Amount'].std()
    fondo_emergencia = std_gastos * 6  # For example: 6 months of expenses

    # Calculate surplus to invest
    total_incomes = df[df['Amount'] > 0]['Amount'].sum()
    total_expenses = df[df['Amount'] < 0]['Amount'].sum()  # Expenses are recorded as negative amounts
    net_savings = total_incomes + total_expenses
    excedente_invertir = net_savings * 0.3  # For example: 20% of net savings

    return gastos_mensuales, expenses_by_category, fondo_emergencia, excedente_invertir
