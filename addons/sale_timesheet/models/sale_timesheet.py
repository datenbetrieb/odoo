# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, api, fields, exceptions
from openerp.tools.translate import _

class ResCompany(models.Model):
    _inherit = 'res.company'
    @api.model
    def _get_uom_hours(self):
        try:
            return self.env.ref("product.product_uom_hour").id
        except ValueError, e:
            return False
    project_time_mode_id = fields.Many2one('product.uom', string='Timesheet UoM', default=_get_uom_hours)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    timesheet_cost = fields.Float(string='Timesheet Cost', default=0.0)

class product_template(models.Model):
    _inherit = 'product.template'
    is_timesheet = fields.Boolean(string="Track Service Time")

    @api.onchange('type', 'invoice_policy')
    def onchange_type_timesheet(self):
        if self.type=='service' and self.invoice_policy=='time material':
            self.is_timesheet = True
        if self.type<>'service':
            self.is_timesheet = False
        return {}


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    @api.multi
    def write(self, values):
        result = super(AccountAnalyticLine, self).write(values)
        if ('unit_amount' in values) and ('amount' not in values):
            for line in self:
                if line.is_timesheet and line.product_id:
                    line.amount = -line.unit_amount * line.product_id.standard_price
        return result

    @api.multi
    def _update_timesheet_line(self):
        sol_obj = self.env['sale.order.line']
        for line in self:
            if line.is_timesheet:
                if not line.so_line:
                    sol = sol_obj.search([
                        ('order_id.project_id','=',line.account_id.id),
                        ('state','=','sale'),
                        ('product_id.is_timesheet','=',True),
                        ('product_id.type','=','service')])
                    if sol:
                        sol = sol[0]
                else:
                    sol = line.so_line
                if sol:
                    cost = 0.0
                    employee_obj = self.env['hr.employee']
                    emp = employee_obj.search([('user_id', '=', line.user_id.id)])
                    if emp:
                        cost = emp[0].timesheet_cost
                    line.write({
                        'product_id': sol.product_id.id,
                        'product_uom_id': self.env.user.company_id.project_time_mode_id.id or sol.product_id.uom_id.id,
                        'amount': -line.unit_amount * timesheet_cost,
                        'so_line': sol.id
                    })
        result = super(AccountAnalyticLine, self)._update_timesheet_line()
        return result

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    @api.constrains('order_line')
    def _check_multi_timesheet(self):
        count = 0
        for line in self.order_line:
            if line.product_id.is_timesheet:
                count+=1
            if count > 1:
                raise UserError(_("You can use only one product on timesheet within the same sale order. You should split your order to include only one contract based on time and material."))
        return {}

    @api.one
    def action_confirm(self):
        result = super(SaleOrder, self).action_confirm()
        if not self.project_id:
            for line in self.order_line:
                if line.product_id.is_timesheet:
                    self._create_analytic_account(prefix=self.product_id.default_code or None)
                    break
        return result



