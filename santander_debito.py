import pandas as pd
import PyPDF2
import tabula
import re
from category_mapping import category_mapping
import numpy as np
from datetime import datetime
month_mapping = {
    'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04',
    'MAY': '05', 'JUN': '06', 'JUL': '07', 'AGO': '08',
    'SEP': '09', 'OCT': '10', 'NOV': '11', 'DIC': '12'
}


def spanish_date_to_datetime(date_str):
    """Convert a Spanish date string to a 'dd/mm/yy' format string."""
    if pd.isna(date_str):
        return None
    for es_month, en_month in month_mapping.items():
        if es_month in date_str.upper():  # Make sure to match uppercase abbreviations
            date_str = date_str.replace(es_month, en_month)
            try:
                date_obj = datetime.strptime(date_str, '%d-%m-%Y')
                return date_obj.strftime('%d/%m/%y')
            except ValueError:
                return None  # Invalid date format
    return None  # Month not found





def clean_monetary_value(value):
    """Remove non-numeric characters, adjust for number formatting, and convert to float."""
    # Convert the value to string, remove commas used for thousands
    cleaned_value = re.sub(r'[^\d.]+', '', str(value).replace(',', ''))
    try:
        # Attempt to convert the cleaned value to float
        return float(cleaned_value)
    except ValueError:
        # Handle cases where the conversion may fail
        return 0


def assign_category(description):
    """Assign category based on description."""
    if pd.isna(description):
        return "Other"  # Return a default category if the description is NaN
    description = str(description)  # Ensure description is a string
    for keyword, category in category_mapping.items():
        if keyword.lower() in description.lower():
            return category
    return "Other"  # Default category if no keyword matches


def extract_and_clean_table(pdf_path, page, area, columns, column_names):
    """Extract and clean table data from a specific page."""
    tables = tabula.read_pdf(pdf_path, pages=page, area=area, columns=columns, guess=False, stream=True)

    if len(tables) == 0:
        return pd.DataFrame(columns=column_names)

    table = tables[0]
    table = table.iloc[:, :len(column_names)].copy()
    table.columns = column_names

    # Convert Date column using the new function
    table['Date'] = table['Date'].apply(spanish_date_to_datetime)

    # Drop rows with invalid dates
    table.dropna(subset=['Date'], inplace=True)

    table['Debit'] = table['Debit'].apply(clean_monetary_value)
    table['Credit'] = table['Credit'].apply(clean_monetary_value)

    # Swap 'Debit' and 'Credit' values
    table['Debit'], table['Credit'] = table['Credit'], table['Debit']

    # Calculate the "Amount" as Credit - Debit for a credit card statement
    table['Amount'] = table['Credit'] - table['Debit']

    # Assign 'Category' based on the description
    table['Category'] = table['Description'].apply(assign_category)

    # Assign 'Category Type' based on the 'Amount' sign
    table['Category Type'] = np.where(table['Amount'] > 0, 'income', 'expenses')

    table.reset_index(drop=True, inplace=True)
    return table


def process_pdf_santander_debito(pdf_path, output_csv_path):
    """Process the entire PDF and save the data to a CSV file."""
    column_names = ["Date", "Folio", "Description", "Debit", "Credit", "Restos"]
    extended_columns = column_names + ["Amount", "Category Type", "Category"]  # Include the new Amount column

    table_area = [100, 25.2, 753.84, 598.56]
    column_boundaries = [79.2, 112.32, 361.44, 429.84, 497.52]

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        number_of_pages = len(reader.pages)

    all_tables = pd.DataFrame(columns=extended_columns)
    for page in range(1, number_of_pages):
        area = table_area
        table = extract_and_clean_table(pdf_path, page, area, column_boundaries, column_names)
        all_tables = pd.concat([all_tables, table], ignore_index=True)

    # Drop unused columns before saving to CSV
    drop_columns = ['Folio', 'Restos']
    all_tables.drop(columns=drop_columns, inplace=True, errors='ignore')
    all_tables.to_csv(output_csv_path, index=False)
