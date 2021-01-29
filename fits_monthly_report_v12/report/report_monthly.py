from odoo import api, fields, models, tools, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from itertools import groupby
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta




class ReportMonthly(models.AbstractModel):
    _name = 'report.fits_monthly_report_v12.report_monthly'




    def get_timesheets(self, docs):
        
        if docs.from_date and docs.to_date:
            rec = self.env['account.analytic.line'].sudo().search([('user_id', '=', docs.employee[0].id),
                                                        ('date', '>=', docs.from_date),('date', '<=', docs.to_date)])
            ide = self.env['idea.junction'].sudo().search([('employee_id', '=', docs.employee[0].id),
                                                        ('date_created', '>=', docs.from_date), ('date_created', '<=', docs.to_date)])
            activity = self.env['monthly.activity'].sudo().search([('employee_id', '=', docs.employee[0].id),
                                                        ('date', '>=', docs.from_date), ('date', '<=', docs.to_date)])
            print( "===========Aktivity============", activity)
            
        elif docs.from_date:
            rec = self.env['account.analytic.line'].sudo().search([('user_id', '=', docs.employee[0].id),
                                                        ('date', '>=', docs.from_date)])
        elif docs.to_date:
            rec = self.env['account.analytic.line'].sudo().search([('user_id', '=', docs.employee[0].id),
                                                            ('date', '<=', docs.to_date)])
        else:
            rec = self.env['account.analytic.line'].sudo().search([('user_id', '=', docs.employee[0].id)])
        
        records = []
        idea = []
        aktivitas = []
        total = 0

        
        for r in rec:
            vals = {'project': r.project_id.name,
                    'user': r.user_id.partner_id.name,
                    'duration': r.unit_amount,
                    'date': r.date,
                    'manager':r.project_id.user_id.name
                    }
           
            total += r.unit_amount
            records.append(vals)
            
        for obj in ide:
            date_created = fields.Date.from_string(obj.date_created)
            idea.append({'date_created': date_created.strftime('%Y-%m-%d'),
                             'idea_details' : obj.idea_details})
            
        for act in activity:
            aktivitas.append({'date': act.date,
                         'detail_activity' : act.detail_activity,
                         'plan_activity' : act.plan_activity})    
        
            
        return [records, total, idea, aktivitas]
    
    
    @api.multi
    def get_next_day(self, day_date):
        """ Get following date of day_date, based on resource.calendar. If no
        calendar is provided, just return the next day.

        :param date day_date: current day as a date

        :return date: next day of calendar, or just next day """
        if not self:
            return day_date + relativedelta(days=1)
        self.ensure_one()
        weekdays = self.get_weekdays()

        base_index = -1
        for weekday in weekdays:
            if weekday > day_date.weekday():
                break
            base_index += 1

        new_index = (base_index + 1) % len(weekdays)
        days = (weekdays[new_index] - day_date.weekday())
        if days < 0:
            days = 7 + days

        return day_date + relativedelta(days=days)

    @api.model
    def _get_report_values(self, docids, data=None):
         
        print ("=============DATA_MONTHLY===============", docids, data)
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        day_from = fields.Datetime.from_string(docs.from_date)
        year = int(day_from.year)
        day_to = fields.Datetime.from_string(docs.to_date)
        year_to = int(day_to.year)
        identification = []
        leave = []
        plan = []
        overtime = []
        att = []
         
        hari_calendar = 0
        kehadiran = 0
        no_check = 0
        terlambat = 0
        lbh_awal = 0  
        half = 0
        message = 0
        workday_hadir = 0
        holiday_hadir = 0
        tot_leave = 0
        tot_unapp = 0
        tot_ts = 0
        tot_absen = 0
        tot_diff = 0
        at_site = 0
        month_met = 0
        ovt_done = 0
        tot_ovt = 0
       
         
         
        obj_employee = self.env['hr.employee'].sudo().search([('user_id', '=', docs.employee[0].id)])
         
        for i in self.env['hr.employee'].sudo().search([('user_id', '=', docs.employee[0].id)]):
            if i:
                identification.append({'id': i.identification_id, 'name': i.name,  
                                        'department' :i.department_id.name, 'job' :i.job_id.name })
                print ('======================PEGAWAI==================', i.name ,i.department_id.name ,i.job_id.name )
                 
        for l in self.env['hr.leave'].sudo().search([('user_id', '=', docs.employee[0].id),
                                                 ('date_from', '>=', docs.from_date),('date_to', '<=', docs.to_date)]):
            date_from = fields.Date.from_string(l.date_from)
            date_to = fields.Date.from_string(l.date_to)
            if l:
                leave.append({'name': l.name,'date_from': date_from.strftime('%Y-%m-%d'),
                               'date_to' :date_to.strftime('%Y-%m-%d'), 'notes' :l.notes,
                               'state' :l.state,'days' :l.number_of_days})
                print ('======================IZIN==================', l.number_of_days)
                 
        for p in self.env['hr.leave'].sudo().search([('user_id', '=', docs.employee[0].id),
                                                 ('date_from', '>', docs.to_date)]):
            date_from = fields.Date.from_string(p.date_from)
            date_to = fields.Date.from_string(p.date_to)
            if p:
                plan.append({'name': p.name,'date_from': date_from.strftime('%Y-%m-%d'),
                               'date_to' :date_to.strftime('%Y-%m-%d'), 'notes' :p.notes,
                               'state' :p.state,'days' :p.number_of_days})
                print ('======================RENCANA CUTI==================', p.number_of_days)
                 
                 
        ot_done = self.env['hr.overtime'].sudo().search([('employee_id','=',obj_employee.id), ('date_from','>=', docs.from_date), 
                                                             ('date_from','<=',docs.to_date),('state','=','validate')])
        for otd in ot_done:
            ovt_done += otd.number_of_hours
     
             
        ot_no_done = self.env['hr.overtime'].sudo().search([('employee_id','=',obj_employee.id), ('date_from','>=', docs.from_date), 
                                                             ('date_from','<=',docs.to_date)])
        for ovt in ot_no_done:
            tot_ovt += ovt.number_of_hours
    
            print ('======================OVERTIME request==================', ovt.number_of_hours)
         
        for ot in self.env['hr.overtime'].sudo().search([('employee_id','=',obj_employee.id), ('date_from','>=', docs.from_date), 
                                                             ('date_from','<=',docs.to_date)]) :
            date_from = fields.Date.from_string(ot.date_from)
            date_to = fields.Date.from_string(ot.date_to)
                 
            if ot:
                overtime.append({'date_from': date_from.strftime('%Y-%m-%d'),
                               'date_to' :date_to.strftime('%Y-%m-%d'), 'notes' :ot.notes,
                               'state' :ot.state,'hours' :ot.number_of_hours,
                               'ovt_done':ovt_done,'tot_ovt':tot_ovt})
                
            print ('======================OVERTIME done==================', tot_ovt)     
 
        obj_sheet = self.env['hr_timesheet.sheet'].sudo().search([('employee_id','=',obj_employee.id), ('date_start','>=', docs.from_date), 
                                                             ('date_end','<=',docs.to_date)])
          
          
        for sheet in obj_sheet :
            obj_sheet_day = obj_sheet = self.env['hr_timesheet_sheet.sheet.day'].sudo().search([('sheet_id','=',sheet.id),('total_attendance','!=',0.0)])
            for sheetday in obj_sheet_day:
                terlambat += sheetday.lambat
                lbh_awal += sheetday.pla
                half += sheetday.hdl
                kehadiran += sheetday.hadir
                no_check += sheetday.no_checkout
                workday_hadir += sheetday.work_day
                holiday_hadir += sheetday.holiday
                # at_site += sheetday.site_office
                # month_met += sheetday.monthly_meeting
                  
            obj_timesheet = obj_sheet = self.env['hr_timesheet_sheet.sheet.day'].sudo().search([('sheet_id','=',sheet.id)])
            for timeatt in obj_timesheet :
                tot_ts += timeatt.total_timesheet
                tot_absen += timeatt.total_attendance
                tot_diff += timeatt.total_difference 
#                 tot_timesheet = int(tot_ts)
#                 tot_attendance = int(tot_absen) 
#                 tot_difference  = int(tot_diff)
                tot_timesheet = tot_ts
                tot_attendance = tot_absen 
                tot_difference  = tot_diff
              
        print ('======================TIMESHEET TOTAL==================', obj_sheet, tot_ts)          
        #leave_obj=self.env['hr.holidays'].search([('employee_id','=',obj_employee.id), ('date_from','>=', docs.from_date), 
        #                                                     ('date_to','<=',docs.to_date),('state','=','validate')])
 
        #for x in leave_obj :
            #tot_leave += x.number_of_days
            #tot_unapp = hari_calendar  - (workday_hadir + tot_leave)
                
                     
         
        
        
        #hadir = []       
        #for ab in self.env['hr.attendance'].search([('employee_id','=',obj_employee.id), ('check_in','>=',docs.from_date), 
        #                                                   ('check_in','<=',docs.to_date)]) :
             
            #date_chek = datetime.strptime(ab.check_in,"%Y-%m-%d %H:%M:%S") + timedelta(hours=7)
            #checkin_str = date_chek.strftime('%Y-%m-%d')
            #hadir.append(checkin_str)
            #absen = list(set(hadir))
            #kehadiran = len(absen)
            #no_check += ab.no_checkout
           
        message_obj=self.env['mail.message'].sudo().search([('model','=', 'project.task'),('author_id.name','=',docs.employee[0].name),
                                                     ('date','>=',docs.from_date), ('date','<=',docs.to_date)])
           
        tgl = []
        for x in message_obj :
            date_mess = datetime.now()
#             date_mess = datetime.strptime(x.date,"%Y-%m-%d %H:%M:%S")
            date_str = date_mess.strftime('%Y-%m-%d')
            tgl.append(date_str)
            send_message = list(set(tgl))
            message = len(send_message)
             
        
            
        holiday_obj=self.env['hr.holidays.public.line'].sudo().search([('year_id.year','=', year),('date','>=',day_from), 
                                                           ('date','<=',day_to)])
          
        holiday_next =self.env['hr.holidays.public.line'].sudo().search([('year_id.year','=', year_to),('date','>=',day_from), 
                                                           ('date','<=',day_to)])
         
        
      
        #nb_of_days = (day_to - day_from).days
        nb_of_days = (day_to - day_from).days + 1
        #nb_of_days = (day_to - day_from).days - 1
        #nb_of_days = (day_to - day_from).days + 5
        #date_start = day_from - relativedelta(days=1)
        date_start = day_from
        hari = []
        for day in range(0, nb_of_days):
            if not obj_employee:
                hari_calendar = 0
            else :    
                working_day = self.get_next_day(date_start + timedelta(days=day))
                print ('======================working day==================', working_day)
                hari.append(working_day)
                days = list(set(hari))
                print ('=========================days===============', days)
                workday = len(days)
                holiday = len(holiday_obj)
                holiday_to = len(holiday_next)
                print ('=========================days===============', workday, holiday, holiday_to)
                hari_calendar = workday - holiday
                  
                  
        leave_obj=self.env['hr.leave'].sudo().search([('employee_id','=',obj_employee.id), ('date_from','>=', docs.from_date), 
                                                             ('date_to','<=',docs.to_date),('state','=','validate')])
  
        for x in leave_obj :
            tot_leave += x.number_of_days
        tot_unapp = hari_calendar  - (workday_hadir + tot_leave)
                  
        att.append({
                    'hari_calendar': hari_calendar,
                    'kehadiran': kehadiran, 
                    'no_checkout' : no_check, 
                    'terlambat': terlambat, 
                    'lbh_awal':lbh_awal, 
                    'half_time': half,
                    'message': message,
                    'workday_hadir': workday_hadir,
                    'holiday_hadir': holiday_hadir,
                    'tot_timesheet': tot_timesheet,
                    'tot_attendance': tot_attendance,
                    'tot_difference': tot_difference,
                    'tot_leave': tot_leave,
                    'tot_unapp': tot_unapp,
                    'at_site': at_site,
                    'month_met': month_met,
                      
                    })

  
        timesheets = self.get_timesheets(docs)
         
        period = None
        if docs.from_date and docs.to_date:
            period = str(docs.from_date) + " To " + str(docs.to_date)
        elif docs.from_date:
            period = str(docs.from_date)
        elif docs.from_date:
            period = str(docs.to_date)

        return  {
           'doc_ids': self.ids,
           'doc_model': self.model,
           'docs': docs,
           'timesheets': timesheets[0],
           'total': timesheets[1],
           'perusahaan': docs.employee[0].company_id.name,
           'identification': identification,
           'leave': leave,
           'overtime': overtime,
           'plan': plan,
           'idea': timesheets[2],
           'aktivitas': timesheets[3],
           'att': att,
           'period': period,
        }
        
#         return self.env['report'].render('fits_monthly_report_v12.monthly_report', docargs)
#         return self.env.ref('fits_monthly_report_v12.action_monthly_report').report_action(self, docargs)
    
