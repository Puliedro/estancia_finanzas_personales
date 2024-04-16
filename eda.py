import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def perform_eda(df):
    """
    Perform exploratory data analysis on the DataFrame.

    Parameters:
    - df: pandas DataFrame containing the transaction data.
    """

    # Vista general de las estadísticas descriptivas
    print(df.describe())

    # Conteo de transacciones por categoría
    print(df['Category'].value_counts())

    # Suma de ingresos y gastos por mes
    df['Month'] = df['Date'].dt.month
    monthly_summary = df.groupby(['Month', 'Category_type'])['Amount'].sum().unstack().fillna(0)
    print(monthly_summary)

    # Visualización de ingresos vs gastos por mes
    monthly_summary.plot(kind='bar', stacked=True)
    plt.title('Ingresos vs Gastos por Mes')
    plt.xlabel('Mes')
    plt.ylabel('Cantidad')
    plt.show()

    # Distribución de los gastos por categoría
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Amount', y='Category', data=df[df['Category_type'] == 'expenses'], estimator=sum, ci=None)
    plt.title('Distribución de Gastos por Categoría')
    plt.xlabel('Total Gastado')
    plt.ylabel('Categoría')
    plt.show()
