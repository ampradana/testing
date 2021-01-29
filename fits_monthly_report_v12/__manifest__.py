# -*- coding: utf-8 -*-
{
    "name": "Timesheet - Monthly Report",
    "version": "1.01",
    "author": "Fits! Team - by PT.Fujicon Priangan Perdana",
    "license": "LGPL-3",
    "category": "Timesheet",
    "website": "https://fujicon-japan.com",
    "depends": ["hr_timesheet","hr_timesheet_sheet","hr_holidays","idea_junction","project",
                 "mail","hr","hr_attendance","hr_overtime_request","fits_timesheet_payroll_v12",
                 "hr_holidays_public"],
    "data": [
            'security/ir.model.access.csv',
            'wizard/monthly_wizard.xml',
            'wizard/message_report_wizard_view.xml',
            'views/summary.xml',
            'views/message_report_view.xml',
            'report/report_monthly.xml',
            'report/monthly_report.xml',    
             ],
    'installable': True,
    'auto_install': False,
}
