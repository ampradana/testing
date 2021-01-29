from odoo import api, fields, models, tools, _


class Activity(models.Model):
    _name = "monthly.activity"
    _rec_name = 'employee_id'
    

    employee_id = fields.Many2one('res.users','Employee',readonly = True, default=lambda self: self.env.user.id)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    detail_activity = fields.Html('Activity Detail')
    plan_activity = fields.Html('work plan ahead')