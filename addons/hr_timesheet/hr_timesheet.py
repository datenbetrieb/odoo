# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, api, fields, exceptions
from openerp.tools.translate import _

class Company(models.Model):
    _inherit = 'res.company'
    timesheet_uom_id = fields.Many2one('product.uom', 'Timesheet UoM')

class account_analytic_line(models.Model):
    _inherit = 'account.analytic.line'
    is_timesheet = fields.Boolean()

    @api.model
    def create(self, values):
        result = super(account_analytic_line, self).create(values)
        result._update_timesheet_line()
        return result

    @api.multi
    def write(self, values):
        result = super(account_analytic_line, self).write(values)
        self._update_timesheet_line()
        return result

    @api.multi
    def _update_timesheet_line(self):
        sol_obj = self.env['sale.order.line']
        for line in self:
            if line.is_timesheet:
                sol = sol_obj.search([
                    ('order_id.project_id','=',result.account_id.id),
                    ('state','=','sale'),
                    ('product_id.invoice_policy','=','time material'),
                    ('product_id.type','=','service')])
                if sol:
                    line.product_id = sol[0].product_id.id
                    line.uom_id = self.env.user.company_id.timesheet_uom_id.id or sol[0].product_uom.id
        return True

class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'
    use_timesheets = fields.Boolean('Timesheets', help="Check this field if this project manages timesheets", deprecated=True)
