# -*- coding: utf-8 -*-
from odoo import http

# class FitsProjectKso(http.Controller):
#     @http.route('/fits_project_kso/fits_project_kso/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fits_project_kso/fits_project_kso/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fits_project_kso.listing', {
#             'root': '/fits_project_kso/fits_project_kso',
#             'objects': http.request.env['fits_project_kso.fits_project_kso'].search([]),
#         })

#     @http.route('/fits_project_kso/fits_project_kso/objects/<model("fits_project_kso.fits_project_kso"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fits_project_kso.object', {
#             'object': obj
#         })