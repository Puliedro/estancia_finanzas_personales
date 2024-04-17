import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_income_expenses_line(df):
    """
    Plots a line chart showing income and expenses over time.

    Args:
    - df: DataFrame with 'Date' and 'Amount' columns, and a 'Category_type' column that has 'income' or 'expenses' categories.

    Returns:
    None
    """
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    monthly_summary = df.groupby(['Month', 'Category_type'])['Amount'].sum().unstack().fillna(0).reset_index()

    fig = px.line(monthly_summary, x='Month', y=['income', 'expenses'], title='Income and Expenses by Month',
                  labels={'value': 'Amount', 'variable': 'Type', 'Month': 'Month'},
                  markers=True)
    fig.show()

def plot_income_expenses_pie(df):
    """
    Plots pie charts for income and expenses by month.

    Args:
    - df: DataFrame with 'Date' and 'Amount' columns, and a 'Category_type' column that has 'income' or 'expenses' categories.

    Returns:
    None
    """
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    df['Net Amount'] = df['Credit'] - df['Debit']

    income_by_month = df[df['Category_type'] == 'income'].groupby('Month')['Net Amount'].sum()
    expenses_by_month = df[df['Category_type'] == 'expenses'].groupby('Month')['Net Amount'].sum().abs()

    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'pie'}, {'type': 'pie'}]],
                        subplot_titles=['Income by Month', 'Expenses by Month'])

    fig.add_trace(go.Pie(labels=income_by_month.index, values=income_by_month.values, name="Income"), 1, 1)
    fig.add_trace(go.Pie(labels=expenses_by_month.index, values=expenses_by_month.values, name="Expenses"), 1, 2)

    fig.update_layout(title_text="Distribution of Income and Expenses by Month")
    fig.show()
