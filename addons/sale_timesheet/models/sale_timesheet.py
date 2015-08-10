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
                if not line.so_line:
                    sol = sol_obj.search([
                        ('order_id.project_id','=',result.account_id.id),
                        ('state','=','sale'),
                        ('product_id.is_timesheet','=',True),
                        ('product_id.type','=','service'])
                    if sol:
                        line.so_line = sol[0]
                        sol = sol[0]
                else:
                    sol = line.so_line
                if sol:
                    line.product_id = sol.product_id.id
                    line.uom_id = self.env.user.company_id.timesheet_uom_id.id or sol.product_uom.id
                    line.amount = -line.unit_amount * sol.product_id.standard_price
        return True

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    @api.constrains('order_line.product_id')
    def _check_children_scope(self):
        count = 0
        for line in self.order_line:
            if line.product_id.is_timesheet:
                count+=1
            if count > 1:
                raise UserError(_("You can use only one product on timesheet within the same sale order. You should split your order to include only one contract based on time and material."))
        return {}

