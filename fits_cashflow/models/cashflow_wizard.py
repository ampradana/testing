from odoo import api, fields, models, _
import xlwt
import base64
import io
from odoo.exceptions import UserError
import time
import datetime


class AccountingCalkReport(models.TransientModel):
    _inherit = "account.common.account.report"
    _name = "accounting.cashflow"
    _description = "Laporan Arus Kas"
    
    date_from = fields.Date(string='Start Date', required=False)
    date_to = fields.Date(string='End Date', required=False)
    periode = fields.Boolean(string='Report Periode')
    initial_balance = fields.Boolean(string='Include Initial Balances', default=False,
                                    help='If you selected date, this field allow you to add a row to display the amount of debit/credit/balance that precedes the filter you\'ve set.')
    sortby = fields.Selection([('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')], string='Sort by', required=True, default='sort_date')
    journal_ids = fields.Many2many('account.journal', 'accounting_cashflow_journal_rel', 'account_id', 'journal_id', string='Journals', required=True)
    
    
    def _get_account_operation_move_entry(self, accounts, init_balance, sortby, display_account):
        """
        :param:
                accounts: the recordset of accounts
                init_balance: boolean value of initial_balance
                sortby: sorting by date or partner and journal
                display_account: type of account(receivable, payable and both)

        Returns a dictionary of accounts with following key and value {
                'code': account code,
                'name': account name,
                'debit': sum of total debit amount,
                'credit': sum of total credit amount,
                'balance': total balance,
                'amount_currency': sum of amount_currency,
                'move_lines': list of move line
        }
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}

        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=self.env.context.get('date_from'), date_to=False, initial_bal=False)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, 0.0 AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                JOIN account_account acc ON (l.account_id = acc.id) \
                WHERE acc.type_cashflow = 'operation' and l.account_id IN %s""" + filters + ' GROUP BY l.account_id')
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
            m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            WHERE acc.type_cashflow = 'operation' and l.account_id IN %s ''' + filters + ''' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)

        return account_res
    
    def _get_operation_values(self,data):
        init_balance = data['form'].get('initial_balance', False)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']

        accounts =  self.env['account.account'].search([])
        dat = self.with_context(data['form'].get('used_context',{}))._get_account_operation_move_entry(accounts, init_balance, sortby, display_account)
    
        return dat
    
    def _get_account_investing_move_entry(self, accounts, init_balance, sortby, display_account):
        """
        :param:
                accounts: the recordset of accounts
                init_balance: boolean value of initial_balance
                sortby: sorting by date or partner and journal
                display_account: type of account(receivable, payable and both)

        Returns a dictionary of accounts with following key and value {
                'code': account code,
                'name': account name,
                'debit': sum of total debit amount,
                'credit': sum of total credit amount,
                'balance': total balance,
                'amount_currency': sum of amount_currency,
                'move_lines': list of move line
        }
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}

        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=self.env.context.get('date_from'), date_to=False, initial_bal=False)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, 0.0 AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                JOIN account_account acc ON (l.account_id = acc.id) \
                WHERE acc.type_cashflow = 'investing' and l.account_id IN %s""" + filters + ' GROUP BY l.account_id')
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
            m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            WHERE acc.type_cashflow = 'investing' and l.account_id IN %s ''' + filters + ''' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)

        return account_res
    
    def _get_investing_values(self,data):
        init_balance = data['form'].get('initial_balance', False)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']

        accounts =  self.env['account.account'].search([])
        dat = self.with_context(data['form'].get('used_context',{}))._get_account_investing_move_entry(accounts, init_balance, sortby, display_account)
    
        return dat
    
    def _get_account_financing_move_entry(self, accounts, init_balance, sortby, display_account):
        """
        :param:
                accounts: the recordset of accounts
                init_balance: boolean value of initial_balance
                sortby: sorting by date or partner and journal
                display_account: type of account(receivable, payable and both)

        Returns a dictionary of accounts with following key and value {
                'code': account code,
                'name': account name,
                'debit': sum of total debit amount,
                'credit': sum of total credit amount,
                'balance': total balance,
                'amount_currency': sum of amount_currency,
                'move_lines': list of move line
        }
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}

        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=self.env.context.get('date_from'), date_to=False, initial_bal=False)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, 0.0 AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                JOIN account_account acc ON (l.account_id = acc.id) \
                WHERE acc.type_cashflow = 'financing' and l.account_id IN %s""" + filters + ' GROUP BY l.account_id')
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
            m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            WHERE acc.type_cashflow = 'financing' and l.account_id IN %s ''' + filters + ''' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)

        return account_res
    
    def _get_financing_values(self,data):
        init_balance = data['form'].get('initial_balance', False)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']

        accounts =  self.env['account.account'].search([])
        dat = self.with_context(data['form'].get('used_context',{}))._get_account_financing_move_entry(accounts, init_balance, sortby, display_account)
    
        return dat
    
    def find_cash_at_beginning(self, form):
        cr = self.env.cr
        accounts = self.env['account.account'].search([('type_cashflow', '!=', False)])
        account_ids = []
        for account in accounts:
            account_ids.append(account['id'])

        sum_deb = 0
        sum_cred = 0
        sum_bal = 0
        for acnt in account_ids:
            query = "SELECT sum(debit) as debit,sum(credit) as credit, sum(debit) - sum(credit)" \
                    "balance from account_move_line aml where aml.account_id = %s"
            vals = []

            if form['date_from']:
                query += " and aml.date<%s"
                vals += [acnt, form['date_from']]
            else:
                vals += [acnt]
            cr.execute(query, tuple(vals))
            values = cr.dictfetchall()

            for vals in values:
                if vals['balance']:
                    sum_deb += vals['debit']
                    sum_cred += vals['credit']
                    sum_bal += vals['balance']

        return sum_deb,sum_cred,sum_bal
    
    def _get_account_net_income_move_entry(self, accounts, init_balance, sortby, display_account):
        """
        :param:
                accounts: the recordset of accounts
                init_balance: boolean value of initial_balance
                sortby: sorting by date or partner and journal
                display_account: type of account(receivable, payable and both)

        Returns a dictionary of accounts with following key and value {
                'code': account code,
                'name': account name,
                'debit': sum of total debit amount,
                'credit': sum of total credit amount,
                'balance': total balance,
                'amount_currency': sum of amount_currency,
                'move_lines': list of move line
        }
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}

        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=self.env.context.get('date_from'), date_to=False, initial_bal=False)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, 0.0 AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                JOIN account_account acc ON (l.account_id = acc.id) \
                WHERE acc.type_cashflow = 'netincome' and l.account_id IN %s""" + filters + ' GROUP BY l.account_id')
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
            m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            WHERE acc.type_cashflow = 'netincome' and l.account_id IN %s ''' + filters + ''' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)

        return account_res
    
    def _get_net_income_values(self,data):
        init_balance = data['form'].get('initial_balance', False)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']

        accounts =  self.env['account.account'].search([])
        dat = self.with_context(data['form'].get('used_context',{}))._get_account_net_income_move_entry(accounts, init_balance, sortby, display_account)
    
        return dat




    def _get_report_values(self,docids,data=None):
        date_to =  datetime.datetime.strptime(data['form']['date_to'], '%Y-%m-%d').date()
        periode = data['form']['periode']
        operation = self._get_operation_values(data)
        investing = self._get_investing_values(data)
        financing = self._get_financing_values(data)
        cash_beginning = self.find_cash_at_beginning(data.get('form'))
        net_income = self._get_net_income_values(data)
        end_date = []
        if data['form']['date_from']:
            from_date = datetime.datetime.strptime(data['form']['date_from'], '%Y-%m-%d').date()
            end_date = from_date - (datetime.timedelta(days=1))
            
        
        

        sum_opr = 0
        for o in operation :
            sum_opr += o['balance'] * -1
            
        sum_investing = 0
        for i in investing :
            sum_investing += i['balance'] * -1
            
        sum_financing = 0
        for f in financing :
            sum_financing += f['balance'] * -1
            
       
        
        sum_income = 0
        for ni in net_income :
            sum_income += ni['balance'] * -1
            
        sum_operation = sum_opr + sum_income
        
        bal_increases = sum_operation + sum_investing + sum_financing
        years_end = bal_increases + -(cash_beginning[2])
            
    

    
    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby', 'periode'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))
        records = self.env[data['model']].browse(data.get('ids', []))
        if self._context.get('report_type') == 'excel':
            operation = self._get_operation_values(data)
            investing = self._get_investing_values(data)
            financing = self._get_financing_values(data)
            cash_beginning = self.find_cash_at_beginning(data.get('form'))
            net_income = self._get_net_income_values(data)
            return self._print_cashflow_excel_report(operation,investing,financing,cash_beginning,net_income)
        else:
            return self.env.ref('fits_cashflow.action_report_cashflow').report_action(records, data=data)
    
    
    @api.multi
    def _print_cashflow_excel_report(self,operation,investing,financing,cash_beginning,net_income):
        filename = 'Laporan Arus Kas'
        filename += '.xls'
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'
        number = xlwt.XFStyle()
        number.num_format_str = '#,##0.00'  
        tgl = self.date_to.strftime("%d %B %Y")
        style_header = xlwt.easyxf(
            "font:height 300; font: name Liberation Sans, bold on,color black; align: horiz center")
        style_sub_header = xlwt.easyxf(
                        "font:bold on,color black;")
        
        tgl_mulai = self.date_from.strftime("%d/%m/%Y")
        tgl_selesai = self.date_to.strftime("%d/%m/%Y") 
        tgl_periode = tgl_mulai +' - '+tgl_selesai
    
        
        worksheet.row(0).height_mismatch = True
        worksheet.row(0).height = 500
        worksheet.row(1).height_mismatch = True
        worksheet.row(1).height = 500
        worksheet.row(2).height_mismatch = True
        worksheet.row(2).height = 500
        worksheet.row(3).height_mismatch = True
        worksheet.row(3).height = 500
        
        #lebar kolom
        worksheet.col(0).width = 10000
        worksheet.col(1).width = 5000
        
        worksheet.write_merge(0, 0, 0, 5, self.company_id.name, style=style_header)
        worksheet.write_merge(1, 1, 0, 5, 'Laporan Arus Kas', style=style_header)
        
        
        if self.periode == True :
            worksheet.write_merge(2, 2, 0, 5, 'PERIODE '+ tgl_periode, style=style_header)
        else :
            worksheet.write_merge(2, 2, 0, 5, self.company_id.header_cashflow+" "+ tgl, style=style_header)
            
        worksheet.write_merge(3, 3, 0, 5, self.company_id.sub_header, style=style_header)
            
        end_date = []
        if self.date_from:
            end_date = self.date_from - (datetime.timedelta(days=1))
            worksheet.write(5,0,'For the Period / Year End', style_sub_header)
            worksheet.write(5,1,end_date,date_format)
            worksheet.write(6,0,'Cash at the beginning of the Period / Year', style_sub_header)
            worksheet.write(6,1,cash_beginning[2] * -1, number)
        
            
        sum_opr = 0
        for o in operation :
            sum_opr += o['balance'] * -1
            
        sum_investing = 0
        for i in investing :
            sum_investing += i['balance'] * -1
            
        sum_financing = 0
        for f in financing :
            sum_financing += f['balance'] * -1
            
       
        
        sum_income = 0
        for ni in net_income :
            sum_income += ni['balance'] * -1
            
        sum_operation = sum_opr + sum_income
        
        bal_increases = sum_operation + sum_investing + sum_financing
        years_end = bal_increases + -(cash_beginning[2])
            
            
        
        worksheet.write(8, 0, 'Operation Activities', style_sub_header)
        worksheet.write(8, 1, sum_operation, number)
        worksheet.write(9, 0, 'Net Income')
        worksheet.write(9, 1, sum_income, number)
        row = 10
        col = 0
        for lines in operation:
            worksheet.write(row, col, lines['name'] )
            worksheet.write(row, col + 1, lines['balance'] * -1, number)
            row += 1
            

        row= row+1    
        worksheet.write(row, 0, 'Investing Activities', style_sub_header)
        worksheet.write(row, 1, sum_investing, number)
        row = row + 1
        col = 0
        for lines in investing:
            worksheet.write(row, col, lines['name'])
            worksheet.write(row, col + 1, lines['balance'] * -1, number)
            row += 1
            
        row= row+1    
        worksheet.write(row, 0, 'Financing Activities', style_sub_header)
        worksheet.write(row, 1, sum_financing, number)
        row = row + 1
        col = 0
        for lines in financing:
            worksheet.write(row, col, lines['name'])
            worksheet.write(row, col + 1, lines['balance'] * -1, number)
            row += 1
            
        worksheet.write(row + 1 ,0,'Net Cash Increases', style_sub_header)
        worksheet.write(row + 1 ,1, bal_increases)
            
        if self.date_from: 
            worksheet.write(row + 2 ,0,'Cash at Year End', style_sub_header) 
            worksheet.write(row + 2 ,1, years_end)
        
            
            
        fp = io.BytesIO()
        workbook.save(fp)

        export_id = self.env['fits.cashflow.excel.report'].create(
            {'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
        res = {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'fits.cashflow.excel.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res
    


    
class AccountAcount(models.Model):
    _inherit = 'account.account'
    
    type_cashflow     = fields.Selection([('operation','Operation'),('investing','Investing'),('financing','Financing'),
                                          ('netincome','Net Income')
                                        ],  string='Type Cash Flow')

  
  
    
    
    
    
