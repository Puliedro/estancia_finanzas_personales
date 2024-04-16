import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def simulate_savings(df):
    # Ensure 'Credit' and 'Debit' are numeric
    df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce')
    df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce')

    # Calculate mean and standard deviation for 'Credit' and 'Debit'
    mean_ingresos = df['Credit'].mean()
    std_ingresos = df['Credit'].std()

    mean_gastos = df['Debit'].mean()
    std_gastos = df['Debit'].std()

    # Simulate scenarios for income and expenses
    ingresos_simulados = np.random.normal(loc=mean_ingresos, scale=std_ingresos, size=1000)
    gastos_simulados = np.random.normal(loc=mean_gastos, scale=std_gastos, size=1000)

    # Simulate savings
    ahorros_simulados = ingresos_simulados - gastos_simulados

    # Plotting the distribution of simulated savings
    sns.histplot(ahorros_simulados, kde=True)
    plt.title('Distribution of Savings')
    plt.xlabel('Savings')
    plt.ylabel('Frequency')
    plt.axvline(np.mean(ahorros_simulados), color='red', linestyle='dashed', linewidth=2)
    plt.axvline(np.median(ahorros_simulados), color='green', linestyle='dashed', linewidth=2)
    plt.legend(['Mean', 'Median'])
    plt.show()

    # Summary statistics
    summary_stats = {
        'mean': np.mean(ahorros_simulados),
        'median': np.median(ahorros_simulados),
        'min': np.min(ahorros_simulados),
        'max': np.max(ahorros_simulados),
        'std_dev': np.std(ahorros_simulados),
        'probability_negative': np.mean(ahorros_simulados < 0)
    }

    return summary_stats