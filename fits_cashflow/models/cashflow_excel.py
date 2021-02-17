# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ExcelCashFlowReport(models.TransientModel):
    _name = "fits.cashflow.excel.report"

    excel_file = fields.Binary('Excel Report')
    file_name = fields.Char('Excel File', size=64)
    
class ResCompany(models.Model):
    _inherit = 'res.company'

    header_cashflow = fields.Char('Sub Header Cash Flow')
    header_calk = fields.Char('Sub Header CALK')
    sub_header = fields.Char('Sub Header 2')