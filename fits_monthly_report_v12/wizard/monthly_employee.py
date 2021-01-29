from odoo import api, fields, models, tools, exceptions, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from itertools import groupby


class EmployeeMonthly(models.TransientModel):
    _name = 'monthly.wizard'
    
    def _default_employee(self):
        emp_ids = self.env['res.users'].search([('id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    employee = fields.Many2one('res.users', string="Employee", default=_default_employee, required=True)
    from_date = fields.Date(string="Starting Date", required=True)
    to_date = fields.Date(string="Ending Date", required=True)

    def print_monthly(self, data):
        """Redirects to the report with the values obtained from the wizard
        'data['form']': name of employee and the date duration"""
        obj_employee = self.env['hr.employee'].search([('user_id', '=', self.employee.id)])
        obj_sheet    = self.env['hr_timesheet.sheet'].search([('employee_id', '=', obj_employee.id), ('date_start', '=', self.from_date),
                                                             ('date_end', '=', self.to_date)])
        
#         records = self.env[self.model].browse(self.env.context.get('active_id'))
        if obj_sheet :
            data = {}
            data['form'] = self.read(['employee', 'from_date', 'to_date'])[0]
            
            return self.env.ref('fits_monthly_report_v12.action_monthly_report').report_action(self, data=data)

        else :
            raise exceptions.ValidationError(("Timesheet Period : %s - %s Not Define\n check again the date of your Timesheet Period to be printed ") % (self.from_date, self.to_date))
    

    
    @api.multi
    def timesheet_lines(self):
       
        obj_timesheet = self.env['account.analytic.line'].search([('user_id', '=', self.employee[0].id),
                                    ('date', '>=', self.from_date), ('date', '<=', self.to_date)])
        
        self.ensure_one()
        report_pages = [[]]
        for category, lines in groupby(obj_timesheet, lambda l: l.project_id):
           
            # Append category to current report page
            report_pages[-1].append({
                'name': category and category.name or 'Uncategorized',
                'manager': category.user_id.name,
                'lines': list(lines)
            })

        return report_pages

