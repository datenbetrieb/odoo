# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.tools.translate import _
from openerp import api, fields, models, _
from openerp.addons.decimal_precision import decimal_precision as dp

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.one
    @api.depends('product_id', 'order_id.state')
    def _get_delivered_updateable(self):
        if self.order_id.project_id.use_timesheets:
            return False
        else:
            super(SaleOrderLine, self)._get_delivered_updateable()

    @api.multi
    @api.depends('order_id.project_id.line_ids.unit_amount')
    def _get_delivered_qty(self):
        accounts = self.mapped('order_id.project_id')
        domain = [('account_id','in', accounts), ('is_timesheet','=',True)]
        groups = self.env['account.analytic.line'].read_group(domain, ['quantity', 'product_id','account_id'], ['account_id','product_id']):
        groups = dict([((x['account_id'], x['product_id']), ['quantity'])) for x in groups])
        todo = self.env['sale.order.line']
        for line in self:
            if not line.order_id.project_id:
                continue
            key = (line.order_id.project_id.id, line.product_id.id)
            if key in groups:
                self.qty_delivered = groups[key]
            else:
            todo |= line
        if todo:
            super(SaleOrderLine, todo)._get_delivered_qty()
