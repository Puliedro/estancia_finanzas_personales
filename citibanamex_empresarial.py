import pandas as pd
import PyPDF2
import tabula
import re
from datetime import datetime
from category_mapping import category_mapping

# Add a dictionary to map Spanish month abbreviations to numbers
month_mapping = {
    'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04',
    'MAY': '05', 'JUN': '06', 'JUL': '07', 'AGO': '08',
    'SEP': '09', 'OCT': '10', 'NOV': '11', 'DIC': '12'
}


def merge_transactions(df):
    # Initialize an empty DataFrame to hold the merged transactions
    merged_df = pd.DataFrame(columns=df.columns)
    temp_row = {}
    for _, row in df.iterrows():
        # If the row has a Date, it's the start of a new transaction
        if pd.notnull(row['Date']):
            # If there is a transaction being built, append it before starting a new one
            if temp_row:
                merged_df = merged_df.append(temp_row, ignore_index=True)
            # Start a new transaction
            temp_row = row.copy()
            temp_row['Description'] = str(row['Description']) if pd.notnull(row['Description']) else ''
        else:
            # If this row is part of an ongoing transaction, merge information
            if 'Description' in row and pd.notnull(row['Description']):
                temp_row['Description'] += ' ' + str(row['Description'])
            # Safely add Debit, Credit, and Amount, ensuring they exist in the row first
            for col in ['Debit', 'Credit', 'Amount']:
                if col in row and pd.notnull(row[col]):
                    temp_row[col] = temp_row.get(col, 0) + row[col]

    # Add the last transaction if it's not empty
    if temp_row:
        merged_df = merged_df.append(temp_row, ignore_index=True)

    # Keep rows with Date as they mark the start of transactions
    merged_df = merged_df[pd.notnull(merged_df['Date'])]
    return merged_df


def assign_category(description):
    """Assign category and category type based on description with prioritized keyword matching."""
    if isinstance(description, str):  # Check if description is a string
        # Sort keys by length in descending order to prioritize more specific (longer) keys
        sorted_keywords = sorted(category_mapping.keys(), key=len, reverse=True)
        for keyword in sorted_keywords:
            if keyword.lower() in description.lower():
                return category_mapping[keyword]
    return "Other", "Other"  # Return default if not a string or if no keyword found




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
    area = [396, 115.2, 410.4, 276.48]
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
    """Convert a 'DD MONTH' format date string to a datetime object, appending the correct year based on month."""
    if not isinstance(date_str, str):
        return None

    # Replace the Spanish month with its numeric representation
    for spanish_month, month_number in month_mapping.items():
        if spanish_month in date_str:
            # Replace the month name with its numeric equivalent and format it correctly
            date_str_numeric_month = date_str.replace(spanish_month, month_number)
            date_str_formatted = date_str_numeric_month.replace(' ', '/')
            # Determine which year to use
            year_to_use = max_year if month_number == '01' and min_year != max_year else min_year
            date_with_year = f"{date_str_formatted}/{year_to_use}"
            try:
                return datetime.strptime(date_with_year, '%d/%m/%Y')
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

    # Convert Date1 and Date columns using the new function
    # Adjust the date conversion call if necessary
    table['Date'] = table['Date'].apply(lambda x: spanish_date_to_datetime(x, min_year, max_year))
    table.dropna(subset=['Description'], inplace=True)
    #table.dropna(subset=['Date'], inplace=True)

    table['Debit'] = table['Debit'].apply(clean_monetary_value)
    table['Credit'] = table['Credit'].apply(clean_monetary_value)
    # Remove specific rows based on description
    indices_to_remove = table[table['Description'] == 'TRASPASO A MESES SIN INTERES'].index - 1
    indices_to_remove = indices_to_remove[indices_to_remove >= 0]
    table.drop(indices_to_remove, inplace=True)

    # Calculate the "Amount" as Debit - Credit
    table['Amount'] = table['Credit'] - table['Debit']

    if not table.empty:
        table['Description'] = table['Description'].fillna('')
        category_results = table['Description'].apply(assign_category)
        table['Category Type'], table['Category'] = zip(*category_results)
    else:
        table['Category Type'], table['Category'] = pd.Series([]), pd.Series([])
    table = merge_transactions(table)
    table.reset_index(drop=True, inplace=True)

    return table




def process_pdf_citibanamex_empresarial(pdf_path, output_csv_path):
    """Process the entire PDF and save the data to a CSV file."""
    min_year, max_year = extract_year_range_from_pdf(pdf_path)
    column_names = ["Date", "Description", "Debit", "Credit", "Restos"]
    extended_columns = column_names + ["Amount", "Category Type", "Category"]  # Include the new Amount column

    table_area_page_2 = [100, 12.24, 753.84, 598.56]  # Page 2
    table_area_other_pages = [100, 12.24, 753.84, 598.56]  # Pages 3 and onwards
    column_boundaries = [52.56, 244.8, 323.28, 401.76, 480.24]


    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        number_of_pages = len(reader.pages)

    all_tables = pd.DataFrame(columns=extended_columns)
    for page in range(1, number_of_pages - 2):
        area = table_area_other_pages
        table = extract_and_clean_table(pdf_path, page, area, column_boundaries, column_names, min_year, max_year)
        all_tables = pd.concat([all_tables, table], ignore_index=True)

    # Drop the 'Restos', 'Date1', and 'Reference' columns before saving to CSV
    drop_columns = ['Restos']
    all_tables.drop(columns=drop_columns, inplace=True, errors='ignore')

    all_tables.to_csv(output_csv_path, index=False)
