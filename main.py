
from bbva_credito import process_pdf_bbva_credito
from bbva_debito import process_pdf_bbva_debito
from santander_debito import process_pdf_santander_debito
from citibanamex_empresarial import process_pdf_citibanamex_empresarial



"""
pdf_path = 'BBVA\BBVA Debito\BBVA Debito_03_2024.pdf'
output_csv_path = 'BBVA\BBVA Debito\BBVA Debito_03_2024.csv'
"""

"""
pdf_path = 'BBVA\BBVA Credito\dic 2023.pdf'
output_csv_path = 'BBVA\BBVA Credito\dic 2023.csv'
"""

"""
pdf_path = 'Citibanamex\Empresarial\Banamex Empresarial.pdf'
output_csv_path = 'Citibanamex\Empresarial\Banamex Empresarial.csv'
"""


pdf_path = 'Santander\Estado de cuenta febrero 2024.pdf'
output_csv_path = 'Santander\Estado de cuenta febrero 2024.csv'


def main(pdf_file):
    #process_pdf_bbva_credito(pdf_file, pdf_file.replace('.pdf', '.csv'))
    #process_pdf_bbva_debito(pdf_file, pdf_file.replace('.pdf', '.csv'))
    #process_pdf_citibanamex_empresarial(pdf_file, pdf_file.replace('.pdf', '.csv'))
    process_pdf_santander_debito(pdf_file, pdf_file.replace('.pdf', '.csv'))
if __name__ == '__main__':
    main(pdf_path)

