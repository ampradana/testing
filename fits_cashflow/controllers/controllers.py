# -*- coding: utf-8 -*-
from odoo import http

# class FitsCashflow(http.Controller):
#     @http.route('/fits_cashflow/fits_cashflow/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fits_cashflow/fits_cashflow/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fits_cashflow.listing', {
#             'root': '/fits_cashflow/fits_cashflow',
#             'objects': http.request.env['fits_cashflow.fits_cashflow'].search([]),
#         })

#     @http.route('/fits_cashflow/fits_cashflow/objects/<model("fits_cashflow.fits_cashflow"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fits_cashflow.object', {
#             'object': obj
#         })