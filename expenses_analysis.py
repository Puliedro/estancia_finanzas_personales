from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
import matplotlib.pyplot as plt


def analyze_expenses(df):
    # Make sure 'Date' is a datetime column and set it as the index
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    # Resample data to monthly level starting with the month's start
    df_monthly = df.resample('MS').sum()

    # You may need to experiment with different orders to find the best for your data
    # The following order is just an example and may not be optimal for your dataset
    arima_order = (1, 1, 1)

    # Fit ARIMA model
    try:
        model = ARIMA(df_monthly['Amount'], order=arima_order)
        model_fit = model.fit()
    except Exception as e:
        print(f"An error occurred while fitting the ARIMA model: {e}")
        return None, None

    # Predictions
    forecast = model_fit.forecast(steps=12)  # Predict the next 12 months
    plt.figure(figsize=(10, 5))
    plt.plot(df_monthly['Amount'], label='Historical')
    plt.plot(forecast, label='Forecast', color='red')
    plt.title('12 Month Forecast')
    plt.legend()
    plt.show()

    # Sum expenses by category
    gastos_por_categoria = df[df['Category_type'] == 'expenses'].groupby(['Category'])['Amount'].sum()

    # Sort expenses to identify the largest spending categories
    gastos_ordenados = gastos_por_categoria.sort_values(ascending=False)
    print(gastos_ordenados)

    return forecast, gastos_ordenados
