from odoo import api, fields, models, tools, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from itertools import groupby
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class hr_employee(models.Model):
    _inherit = 'hr.employee'
    

    day_work        = fields.Integer(compute='_calc_day_work', string='Work Day')
    kehadiran       = fields.Integer(compute='_calc_att', string='Kehadiran')
    at_site         = fields.Integer(compute='_calc_att', string='at Site Office')
    workday_hadir   = fields.Integer(compute='_calc_att', string='Workday (weekday)')
    holiday_hadir   = fields.Integer(compute='_calc_att', string='Workday (holiday)')
    no_check        = fields.Integer(compute='_calc_att', string='No Checkout')
    terlambat       = fields.Integer(compute='_calc_att', string='T')
    pla             = fields.Integer(compute='_calc_att', string='PLA')
    hdl             = fields.Integer(compute='_calc_att', string='HDL')
    mess            = fields.Integer(compute='_calc_message', string='Report Message')
    period          = fields.Char(compute='_calc_message',string ='Periode')
    leave           = fields.Integer(compute='_calc_leave', string='Total Leave')
    unapproved      = fields.Integer(compute='_calc_leave', string='Unapproved')




    @api.one
    def _calc_day_work(self, data=None):
        if not self.resource_calendar_id:
            return {}
        
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        day_from = fields.Datetime.from_string(docs.from_date)
        year = int(day_from.year)
        day_to = fields.Datetime.from_string(docs.to_date)
        year_to = int(day_to.year)
        
        holiday_obj=self.env['hr.holidays.public.line'].search([('year_id.year','=', year),('date','>=',day_from), 
                                                           ('date','<=',day_to)])
        
        holiday_next =self.env['hr.holidays.public.line'].search([('year_id.year','=', year_to),('date','>=',day_from), 
                                                           ('date','<=',day_to)])
     
        nb_of_days = (day_to - day_from).days
        date_start = day_from - relativedelta(days=1)
        hari = []
        for day in range(0, nb_of_days):
            working_day = str(date_start + timedelta(days=day))
            hari.append(working_day)
            days = list(set(hari))
            workday = len(days)
            holiday = len(holiday_obj)
            holiday_to = len(holiday_next)
            day_work = workday - holiday
    
            
            
    @api.one
    def _calc_att(self, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        tgl_mulai = docs.from_date
        tgl_selesai = docs.to_date
        kehadiran = 0
        no_check = 0
        terlambat = 0
        lbh_awal = 0  
        half = 0
        workday_hadir = 0
        holiday_hadir = 0
        at_site = 0
       
        
                    
                    
        obj_sheet = self.env['hr_timesheet.sheet'].search([('employee_id','=',self.id), ('date_start','>=', tgl_mulai),
                                                             ('date_end','<=',tgl_selesai)])
        
        
        for sheet in obj_sheet :
            obj_sheet_day = obj_sheet = self.env['hr_timesheet_sheet.sheet.day'].search([('sheet_id','=',sheet.id),('total_attendance','!=',0.0)])
            for sheetday in obj_sheet_day:
                terlambat += sheetday.lambat
                lbh_awal += sheetday.pla
                half += sheetday.hdl
                kehadiran += sheetday.hadir
                no_check += sheetday.no_checkout
                workday_hadir += sheetday.work_day
                holiday_hadir += sheetday.holiday
                # at_site += sheetday.site_office
                
            self.kehadiran = kehadiran
            # self.at_site = at_site
            self.terlambat = terlambat
            self.pla = lbh_awal
            self.hdl = half
            self.no_check = no_check
            self.workday_hadir = workday_hadir
            self.holiday_hadir = holiday_hadir
                    
        
                    
                    
    @api.one
    def _calc_message(self, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        tgl_mulai = docs.from_date
        tgl_selesai = docs.to_date
        # var_period = docs.from_date+' - '+docs.to_date
        # var_period = str(self.from_date) + ' - ' + str(self.to_date)
        var_period = str(docs.from_date) + ' - ' + str(docs.to_date)
        self.period = var_period

         
        message_obj=self.env['mail.message'].search([('model','=', 'project.task'),('author_id.name','=',self.user_id.name),
                                                     ('date','>=',tgl_mulai), ('date','<=',tgl_selesai)])
        tgl = []
        for x in message_obj :
            # date_mess = datetime.strptime(x.date,"%Y-%m-%d %H:%M:%S")
            date_mess = datetime.now()
            date_str = date_mess.strftime('%Y-%m-%d')
            tgl.append(date_str)
            message = list(set(tgl))
            self.mess = len(message)
            
            
    @api.one
    def _calc_leave(self, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        tgl_mulai = docs.from_date
        tgl_selesai = docs.to_date
        tot_leave = 0
        tot_unapp = 0
        
        leave_obj=self.env['hr.leave'].search([('employee_id','=',self.id), ('date_from','>=', tgl_mulai),
                                                             ('date_to','<=',tgl_selesai),('state','=','validate')])

        for x in leave_obj :
            tot_leave += x.number_of_days
            
            
        self.leave = tot_leave 
        tot_unapp = self.day_work - (self.workday_hadir + self.leave)
        self.unapproved = tot_unapp
            
