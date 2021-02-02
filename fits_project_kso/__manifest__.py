{
    "name": "Project KSO",
    "version": "12.0_2021.02.02",
    "author": "Fits! Team - by PT.Fujicon Priangan Perdana",
    "license": "LGPL-3",
    'summary': 'Addons Akses Project KSO version 12',
    'description': '''
    Migrasi Addons Project KSO dari Odoo v10 ke Odoo v12

    ''',
    "category": "Project",
    "website": "https://fujicon-japan.com",
    "depends": ["base","project","purchase","account","hr_expense","sale","employee_expense_advance","hr_expense","account","fits_to_do_today",
                "fits_project_budget_v12"],
    "data": [
             'security/ir.model.access.csv',
             'security/group.xml',
             'views/custom_view.xml',
             ],
    'installable': True,
    'auto_install': False,
}