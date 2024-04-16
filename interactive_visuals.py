import pandas as pd
import plotly.express as px

df = pd.read_csv('Anual 2023.csv', parse_dates=['Date'])  # Asegúrate de que 'Date' es la columna de fecha

# Convertir la fecha a un período mensual y luego a cadena de texto para la serialización
df['Month'] = df['Date'].dt.to_period('M').astype(str)
monthly_summary = df.groupby(['Month', 'Category Type'])['Amount'].sum().unstack().fillna(0).reset_index()

# Generar el gráfico
fig = px.line(monthly_summary, x='Month', y=['income', 'expenses'], title='Ingresos y Gastos por Mes',
              labels={'value': 'Monto', 'variable': 'Tipo', 'Month': 'Mes'},
              markers=True)

# Mostrar el gráfico
fig.show()


import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Preparar los datos
df['Month'] = df['Date'].dt.to_period('M').astype(str)  # Creamos una representación de cadena para el mes
df['Amount'] = df['Credit'] - df['Debit']  # Calculamos el monto neto

# Sumar los totales de ingresos y gastos por mes
income_by_month = df[df['Category Type'] == 'income'].groupby('Month')['Amount'].sum()
expenses_by_month = df[df['Category Type'] == 'expenses'].groupby('Month')['Amount'].sum().abs()  # Tomamos el valor absoluto para los gastos

# Generar los gráficos de pastel
fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'pie'}, {'type': 'pie'}]],
                    subplot_titles=['Ingresos por Mes', 'Gastos por Mes'])

# Gráfico de pastel para ingresos
fig.add_trace(go.Pie(labels=income_by_month.index, values=income_by_month.values, name="Ingresos"), 1, 1)

# Gráfico de pastel para gastos
fig.add_trace(go.Pie(labels=expenses_by_month.index, values=expenses_by_month.values, name="Gastos"), 1, 2)

# Personalizar el layout y añadir título
fig.update_layout(title_text="Distribución de Ingresos y Gastos por Mes")

# Mostrar la figura
fig.show()