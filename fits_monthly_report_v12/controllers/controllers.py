# -*- coding: utf-8 -*-
from odoo import http

# class FitsMonthlyReport(http.Controller):
#     @http.route('/fits_monthly_report/fits_monthly_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fits_monthly_report/fits_monthly_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fits_monthly_report.listing', {
#             'root': '/fits_monthly_report/fits_monthly_report',
#             'objects': http.request.env['fits_monthly_report.fits_monthly_report'].search([]),
#         })

#     @http.route('/fits_monthly_report/fits_monthly_report/objects/<model("fits_monthly_report.fits_monthly_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fits_monthly_report.object', {
#             'object': obj
#         })