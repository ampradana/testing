from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _order = "project_id asc"
    

#class HRHoliday(models.Model):
    #_inherit = 'hr.holidays'
    
    #catatan = fields.Text('Note')
    

