import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


import base64
from io import BytesIO

def perform_eda(df):
    """
    Perform exploratory data analysis on the DataFrame and return plots as base64 strings.

    Parameters:
    - df: pandas DataFrame containing the transaction data.

    Returns:
    - A dictionary containing base64 encoded strings for each plot.
    """
    plots = {}

    # Suma de ingresos y gastos por mes
    df['Month'] = df['Date'].dt.month
    monthly_summary = df.groupby(['Month', 'Category_type'])['Amount'].sum().unstack().fillna(0)

    # Visualización de ingresos vs gastos por mes
    plt.figure(figsize=(10, 6))
    monthly_summary.plot(kind='bar', stacked=True)
    plt.title('Ingresos vs Gastos por Mes')
    plt.xlabel('Mes')
    plt.ylabel('Cantidad')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plots['monthly_income_expenses'] = base64.b64encode(buf.getvalue()).decode('utf8')
    plt.close()

    # Distribución de los gastos por categoría
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Amount', y='Category', data=df[df['Category_type'] == 'expenses'], estimator=sum, ci=None)
    plt.title('Distribución de Gastos por Categoría')
    plt.xlabel('Total Gastado')
    plt.ylabel('Categoría')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plots['expense_distribution'] = base64.b64encode(buf.getvalue()).decode('utf8')
    plt.close()

    return plots
