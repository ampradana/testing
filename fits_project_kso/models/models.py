# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountAnalytic(models.Model):
    _inherit = 'account.analytic.account'   
     

    mitra_ids = fields.Many2many('res.users',string='Allow Mitra')
    
class Invoice(models.Model):
    _inherit = "account.invoice"
    
    mitra_ids = fields.Many2many('res.users',string='Allow Mitra')

    account_analytic_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        compute="_compute_analytic_account",
        inverse="_inverse_analytic_account",store=True,
        help="This account will be propagated to all lines, if you need "
        "to use different accounts, define the account at line level.",
    )
    
    @api.multi
    @api.onchange('account_analytic_id')
    def account_analytic_id_change(self):
        if self.account_analytic_id :
            self.mitra_ids = self.account_analytic_id.mitra_ids

    @api.depends("invoice_line_ids.account_analytic_id")
    def _compute_analytic_account(self):
        for rec in self:
            account = rec.mapped("invoice_line_ids.account_analytic_id")
            if len(account) == 1:
                rec.account_analytic_id = account
            else:
                rec.account_analytic_id = False

    def _inverse_analytic_account(self):
        for rec in self:
            if rec.account_analytic_id:
                for line in rec.invoice_line_ids:
                    line.account_analytic_id = rec.account_analytic_id
                    

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    
    mitra_ids = fields.Many2many('res.users',string='Allow Mitra')

    account_analytic_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        compute="_compute_analytic_account",
        inverse="_inverse_analytic_account",
        help="This account will be propagated to all lines, if you need "
        "to use different accounts, define the account at line level.",
    )
    
    
    @api.multi
    @api.onchange('account_analytic_id')
    def account_analytic_id_change(self):
        if self.account_analytic_id :
            self.mitra_ids = self.account_analytic_id.mitra_ids

    @api.depends("order_line.account_analytic_id")
    def _compute_analytic_account(self):
        for rec in self:
            account = rec.mapped("order_line.account_analytic_id")
            if len(account) == 1:
                rec.account_analytic_id = account
            else:
                rec.account_analytic_id = False

    def _inverse_analytic_account(self):
        for rec in self:
            if rec.account_analytic_id:
                for line in rec.order_line:
                    line.account_analytic_id = rec.account_analytic_id
                    
class AdvanceExpense(models.Model):
    _inherit = "employee.advance.expense"
    
    
    mitra_ids = fields.Many2many('res.users',string='Allow Mitra')

    account_analytic_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account")
                    
    @api.multi
    @api.onchange('account_analytic_id')
    def account_analytic_id_change(self):
        if self.account_analytic_id :
            self.mitra_ids = self.account_analytic_id.mitra_ids
            
class EmployeeExpense(models.Model):
    _inherit = "employee.advance.expense"
    
    
    mitra_ids = fields.Many2many('res.users',string='Allow Mitra')

    account_analytic_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account")
                    
    @api.multi
    @api.onchange('account_analytic_id')
    def account_analytic_id_change(self):
        if self.account_analytic_id :
            self.mitra_ids = self.account_analytic_id.mitra_ids
            
class HrExpense(models.Model):
    _inherit = "hr.expense"
    
    mitra_ids = fields.Many2many('res.users',string='Allow Mitra')
    
    @api.multi
    @api.onchange('analytic_account_id')
    def analytic_account_id_change(self):
        if self.analytic_account_id :
            self.mitra_ids = self.analytic_account_id.mitra_ids
            
class HrExpenseReport(models.Model):
    _inherit = "hr.expense.sheet"
    
    mitra_ids = fields.Many2many('res.users',string='Allow Mitra')
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', 
                                      required=True, default=None,
                                      states={'done': [('readonly', True)], 'post': [('readonly', True)]})
    account_analytic_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        compute="_compute_analytic_account",
        inverse="_inverse_analytic_account",
        help="This account will be propagated to all lines, if you need "
        "to use different accounts, define the account at line level.",
    )
    
#     @api.multi
#     def refuse_expenses(self, reason):
#         if not self.user_has_groups('hr_expense.group_hr_expense_user') and not self.user_has_groups('fits_project_kso.group_project_kso_manager'):
#             raise UserError(_("Only HR Officers And KSO can refuse expenses"))
#         self.write({'state': 'cancel'})
#         for sheet in self:
#             body = (_("Your Expense %s has been refused.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (sheet.name, reason))
#             sheet.message_post(body=body)
    
    @api.multi
    @api.onchange('account_analytic_id')
    def account_analytic_id_change(self):
        if self.account_analytic_id :
            self.mitra_ids = self.account_analytic_id.mitra_ids

    @api.depends("expense_line_ids.analytic_account_id")
    def _compute_analytic_account(self):
        for rec in self:
            account = rec.mapped("expense_line_ids.analytic_account_id")
            if len(account) == 1:
                rec.account_analytic_id = account
            else:
                rec.account_analytic_id = False

    def _inverse_analytic_account(self):
        for rec in self:
            if rec.account_analytic_id:
                for line in rec.expense_line_ids:
                    line.analytic_account_id = rec.account_analytic_id
                    
class AssetAsset(models.Model):
    _inherit = "asset.asset"
    
    
    mitra_ids = fields.Many2many('res.users',string='Allow Mitra')

    account_analytic_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account")
                    
    @api.multi
    @api.onchange('account_analytic_id')
    def account_analytic_id_change(self):
        if self.account_analytic_id :
            self.mitra_ids = self.account_analytic_id.mitra_ids
            
class AccountAccount(models.Model):
    _inherit = "account.account"
    
    
    mitra_ids = fields.Many2many('res.users',string='Allow Mitra')
    

class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    
    mitra_ids = fields.Many2many('res.users',string='Allow Mitra')
    
class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"
    
class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"
    
class TodoTodayLine(models.Model):
    _inherit = "todo.today.line"
    
    
    mitra_ids = fields.Many2many('res.users',string='Allow Mitra')
                    
    @api.multi
    @api.onchange('project_id')
    def account_project_id_change(self):
        if self.project_id :
            self.mitra_ids = self.project_id.mitra_ids
            
class ProjectBudget(models.Model):
    _inherit = "fits.project.budget"
    
    
    mitra_ids = fields.Many2many('res.users',string='Allow Mitra')
                    
    @api.multi
    @api.onchange('analytic_account_id')
    def account_analytic_account_id_change(self):
        if self.analytic_account_id :
            self.mitra_ids = self.analytic_account_id.mitra_ids
    
    
            
                    