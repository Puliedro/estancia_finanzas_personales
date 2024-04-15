import tabula
import re
from datetime import datetime


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
            print(f"Minimum Year: {min_year}, Maximum Year: {max_year}")
            return (min_year, max_year)

    # Return a default value if no years are found
    return ("1900", "1900")


# Example of using the function
  # The area in points

