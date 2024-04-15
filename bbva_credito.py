import pandas as pd
import PyPDF2
import tabula
import re
from category_mapping import category_mapping
import numpy as np


def clean_monetary_value(value):
    """Remove non-numeric characters and convert to float."""
    cleaned_value = re.sub(r'[^\d.]+', '', str(value))
    return float(cleaned_value) if cleaned_value else 0


def assign_category(description):
    """Assign category based on description."""
    for keyword, category in category_mapping.items():
        if keyword.lower() in description.lower():
            return category
    return "Other"  # Default category if no keyword matche


def extract_and_clean_table(pdf_path, page, area, columns, column_names):
    """Extract and clean table data from a specific page."""
    tables = tabula.read_pdf(pdf_path, pages=page, area=area, columns=columns, guess=False, stream=True)

    if len(tables) == 0:
        return pd.DataFrame(columns=column_names)

    table = tables[0]
    table = table.iloc[:, :len(column_names)].copy()
    table.columns = column_names

    # Convert dates and clean monetary values
    table['Date1'] = pd.to_datetime(table['Date1'], errors='coerce', format='%d/%m/%y')
    table['Date'] = pd.to_datetime(table['Date'], errors='coerce', format='%d/%m/%y')
    table.dropna(subset=['Date1', 'Date'], inplace=True)
    table['Debit'] = table['Debit'].apply(clean_monetary_value)
    table['Credit'] = table['Credit'].apply(clean_monetary_value)

    # Calculate the "Amount" as Credit - Debit for a credit card statement
    table['Amount'] = table['Credit'] - table['Debit']

    # Assign 'Category' based on the description
    table['Category'] = table['Description'].apply(assign_category)

    # Remove specific rows based on description
    indices_to_remove = table[table['Description'] == 'TRASPASO A MESES SIN INTERES'].index - 1
    indices_to_remove = indices_to_remove[indices_to_remove >= 0]
    table.drop(indices_to_remove, inplace=True)

    # Assign 'Category Type' based on the 'Amount' sign
    table['Category Type'] = np.where(table['Amount'] > 0, 'income', 'expenses')

    table.reset_index(drop=True, inplace=True)
    return table


def process_pdf_bbva_credito(pdf_path, output_csv_path):
    """Process the entire PDF and save the data to a CSV file."""
    column_names = ["Date1", "Date", "Description", "RFC", "Reference", "Debit", "Credit"]
    extended_columns = column_names + ["Amount", "Category Type", "Category"]  # Include the new Amount column

    table_area = [100, 25.2, 753.84, 598.56]
    column_boundaries = [89.28, 151.2, 331.2, 417.6, 477.36, 534.96, 602.64]

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        number_of_pages = len(reader.pages)

    all_tables = pd.DataFrame(columns=extended_columns)
    for page in range(2, number_of_pages - 2):
        area = table_area
        table = extract_and_clean_table(pdf_path, page, area, column_boundaries, column_names)
        all_tables = pd.concat([all_tables, table], ignore_index=True)

    # Drop unused columns before saving to CSV
    drop_columns = ['Restos', 'Date1', 'Reference', 'RFC']  # Assuming 'Restos' needs to be dropped
    all_tables.drop(columns=drop_columns, inplace=True, errors='ignore')

    all_tables.to_csv(output_csv_path, index=False)
