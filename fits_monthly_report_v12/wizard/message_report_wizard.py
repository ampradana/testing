from odoo import api, fields, models, tools, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from itertools import groupby


class MessageWizard(models.TransientModel):
    _name = 'message.report.wizard'
    
    from_date = fields.Date(string="Starting Date", required=True)
    to_date = fields.Date(string="Ending Date", required=True)

    def action_apply(self):
        w_from = self.from_date
        w_to = self.to_date
        data = {}
        data['form'] = self.read(['from_date', 'to_date'])[0]
        return {
                'type': 'ir.actions.act_window',
                'name': 'Report Message',
                'res_model': 'mail.message',
                'domain':[('date','>=',w_from),('date','<=',w_to),('model','=','project.task') ],
                'view_mode': 'tree',
                'view_id': self.env.ref('fits_monthly_report_v12.view_report_message_tree').id,
                'context': {'search_default_author': 1, 'search_default_date': 1}
                }
    
   
    def apply_report(self, data):
        """Redirects to the report with the values obtained from the wizard
        'data['form']': name of employee and the date duration"""
        data = {}
        data['form'] = self.read(['from_date', 'to_date'])[0]
        var_period = 'Periode'+str(self.from_date)+' - '+str(self.to_date)
        return {
                'type': 'ir.actions.act_window',
                'name': var_period,
                'res_model': 'hr.employee',
                'view_mode': 'tree',
                'view_id': self.env.ref('fits_monthly_report_v12.view_report_message_tree').id
                } 
        
        
   
   
    
    
    
    

