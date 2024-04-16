import pandas as pd
import PyPDF2
import tabula
import re
import numpy as np
from datetime import datetime
from category_mapping import category_mapping

# Add a dictionary to map Spanish month abbreviations to numbers
month_mapping = {
    'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04',
    'MAY': '05', 'JUN': '06', 'JUL': '07', 'AGO': '08',
    'SEP': '09', 'OCT': '10', 'NOV': '11', 'DIC': '12'
}

def assign_category(description):
    """Assign category and category type based on description with prioritized keyword matching."""
    # Sort keys by length in descending order to prioritize more specific (longer) keys
    sorted_keywords = sorted(category_mapping.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword.lower() in description.lower():
            return category_mapping[keyword]
    return "Other"  # Ensure it always returns two values



def extract_year_range_from_pdf(pdf_path):
    """
    Extracts a date range string from a specified area in a PDF and returns the minimum and maximum years.

    Args:
    - pdf_path: Path to the PDF file.
    - area: The area to extract text from, specified as [top, left, bottom, right] in points.

    Returns:
    - A tuple containing the minimum and maximum years as strings. If only one year is found, both values in the tuple will be the same.
    """
    # Use tabula to extract text from the specified area
    area = [44.64, 439.2, 64.8, 599.76]
    dfs = tabula.read_pdf(pdf_path, pages=1, area=[area], guess=False, stream=True, multiple_tables=True)

    if dfs:
        # Assuming the first DataFrame contains the text we need
        text = dfs[0].to_string()
        # Find all years in the extracted text
        years = re.findall(r'\b\d{4}\b', text)

        if years:
            min_year = min(years)
            max_year = max(years)
            #print(f"Minimum Year: {min_year}, Maximum Year: {max_year}")
            return (min_year, max_year)

    # Return a default value if no years are found
    return ("1900", "1900")




def spanish_date_to_datetime(date_str, min_year, max_year):
    """Convert a 'DD/MONTH' format date string to a formatted date string in 'dd/mm/yy', appending the correct year based on month."""
    if not isinstance(date_str, str):
        return None

    for spanish_month, month_number in month_mapping.items():
        if spanish_month in date_str:
            date_str_numeric_month = date_str.replace(spanish_month, month_number)
            # Determine which year to use
            year_to_use = min_year if month_number != '01' or min_year == max_year else max_year
            date_with_year = f"{date_str_numeric_month}/{year_to_use}"
            try:
                # Parse the date and convert it to the desired format
                parsed_date = datetime.strptime(date_with_year, '%d/%m/%Y')
                return parsed_date.strftime('%d/%m/%y')  # Changed format here
            except ValueError:
                return None
    return None

def clean_monetary_value(value):
    """Remove non-numeric characters and convert to float. Handle cases where result is just a decimal point."""
    cleaned_value = re.sub(r'[^\d.]+', '', str(value))
    try:
        # Attempt to convert the cleaned string to float
        return float(cleaned_value)
    except ValueError:
        # Return 0.0 if conversion fails (e.g., empty string or only a '.')
        return 0.0


def extract_and_clean_table(pdf_path, page, area, columns, column_names, min_year, max_year):
    """Extract and clean table data from a specific page."""
    tables = tabula.read_pdf(pdf_path, pages=page, area=area, columns=columns, guess=False, stream=True,
                             multiple_tables=True)

    if len(tables) == 0:
        return pd.DataFrame(columns=column_names)

    table = tables[0]
    table = table.iloc[:, :len(column_names)].copy()
    table.columns = column_names

    # Convert Date columns using the new function
    table['Date1'] = table['Date1'].apply(lambda x: spanish_date_to_datetime(x, min_year, max_year))
    table['Date'] = table['Date'].apply(lambda x: spanish_date_to_datetime(x, min_year, max_year))
    table['Debit'] = table['Debit'].apply(clean_monetary_value)
    table['Credit'] = table['Credit'].apply(clean_monetary_value)
    table.dropna(subset=['Date1', 'Date'], inplace=True)

    # Remove specific rows based on description
    indices_to_remove = table[table['Description'] == 'TRASPASO A MESES SIN INTERES'].index - 1
    indices_to_remove = indices_to_remove[indices_to_remove >= 0]
    table.drop(indices_to_remove, inplace=True)

    # Calculate the "Amount" as Debit - Credit
    table['Amount'] = table['Credit'] - table['Debit']

    # Assign 'Category Type' based on the 'Amount' sign
    table['Category Type'] = np.where(table['Amount'] > 0, 'income', 'expenses')

    # Assign 'Category' based on the description
    table['Category'] = table['Description'].apply(assign_category)

    table.reset_index(drop=True, inplace=True)
    return table





def process_pdf_bbva_debito(pdf_path, output_csv_path):
    """Process the entire PDF and save the data to a CSV file."""
    min_year, max_year = extract_year_range_from_pdf(pdf_path)
    column_names = ["Date", "Date1", "Description", "Reference", "Debit", "Credit", "Restos"]
    extended_columns = column_names + ["Amount", "Category Type", "Category"]  # Include the new Amount column

    table_area = [100, 12.24, 753.84, 598.56]
    column_boundaries = [54.72, 100.8, 298.08, 378, 418, 462.24]

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        number_of_pages = len(reader.pages)

    all_tables = pd.DataFrame(columns=extended_columns)
    for page in range(1, number_of_pages - 2):
        area = table_area
        table = extract_and_clean_table(pdf_path, page, area, column_boundaries, column_names, min_year, max_year)
        all_tables = pd.concat([all_tables, table], ignore_index=True)

    # Drop the 'Restos', 'Date1', and 'Reference' columns before saving to CSV
    drop_columns = ['Restos', 'Date1', 'Reference']
    all_tables.drop(columns=drop_columns, inplace=True, errors='ignore')

    all_tables.to_csv(output_csv_path, index=False)
