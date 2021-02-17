{
    "name": "Cash Flow Statement",
    "version": "1.01",
    "author": "Fits! Team - by PT. Fujicon Priangan Perdana",
    "license": "",
    "category": "Account",
    "website": "http://fujicon-japan.com",
    "depends": ['account','bi_financial_pdf_reports'],
    "data": [
            'security/ir.model.access.csv',
            'views/cashflow_excel_view.xml',
            'views/cashflow_wizard_view.xml',
            'report/cashflow_reports.xml',
            'report/report_cashflow.xml',
             ],
    'installable': True,
    'auto_install': False,
}
