from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def analyze_expenses(df):
    # Ensure 'Date' is a datetime column and set it as the index
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    # Resample data to monthly level starting with the month's start
    df_monthly = df.resample('MS').sum()

    # Example ARIMA order
    arima_order = (1, 1, 1)

    # Fit ARIMA model
    try:
        model = ARIMA(df_monthly['Amount'], order=arima_order)
        model_fit = model.fit()
    except Exception as e:
        print(f"An error occurred while fitting the ARIMA model: {e}")
        return None, "An error occurred while fitting the model"

    # Generate forecast
    forecast = model_fit.forecast(steps=12)  # Predict the next 12 months

    # Create plot
    plt.figure(figsize=(10, 5))
    plt.plot(df_monthly['Amount'], label='Historical')
    plt.plot(forecast, label='Forecast', color='red')
    plt.title('12 Month Expense Forecast')
    plt.legend()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plot_url = base64.b64encode(buf.getvalue()).decode('utf8')
    plt.close()

    return plot_url


