# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, api, fields, exceptions
from openerp.tools.translate import _


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def create(self, values):
        result = super(AccountAnalyticLine, self).create(values)
        result._update_timesheet_line()
        return result

    @api.multi
    def write(self, values):
        result = super(AccountAnalyticLine, self).write(values)
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


