# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from openerp import api, fields, models, _

from openerp.tools.translate import _


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    so_line = fields.Many2one('sale.order.line', string='Sale Order Line')

    @api.multi
    def write(self, values):
        if ('unit_amount' in values) or ('so_line' in values):
            oldvalues = dict([(x.id, x.unit_amount) for x in self])
        result = super(AccountAnalyticLine, self).write(values)
        if ('unit_amount' not in values) and ('so_line' not in values):
            return result
        for line in self:
            if (line.amount > 0) or (not line.so_line):
                continue
            qty = self.env['product.uom']._compute_qty_obj(line.product_uom_id, line.unit_amount, line.so_line.product_uom)
            line.so_line.qty_delivered = line.so_line.qty_delivered + line.unit_amount - oldvalues.get(line.id, )
        return result

    @api.model
    def create(self, values):
        line = super(AccountAnalyticLine, self).create(values)
        if (line.amount > 0) or not line.product_id:
            return line
        if line.product_id.invoice_policy not in ('time material','expense','ordered'):
            return line
        if (line.product_id.invoice_policy == 'ordered') and (line.product_id.type in ('product', 'consu')):
            return line

        sol_obj = self.env['sale.order.line']
        if line.product_id.invoice_policy in ('time material', 'ordered'):
            sol = sol_obj.search([('order_id.project_id','=',line.account_id.id),('state','=','sale'),('product_id','=',line.product_id.id)])
            if sol:
                qty = self.env['product.uom']._compute_qty_obj(line.product_uom_id, line.unit_amount, sol[0].product_uom)
                sol[0].qty_delivered += qty
                line.so_line = sol[0].id
                return line

        if line.product_id.invoice_policy == 'ordered':
            return line

        so_obj = self.env['sale.order']
        order = sol_obj.search([('project_id','=',line.account_id.id),('state','=','sale')])

        last_so_line = sol_obj.search([('order_id','=',order[0].id)], _order='sequence desc', limit=1)
        last_sequence = 100
        if last_so_line:
            last_sequence = last_so_line.sequence + 1

        fpos = order[0].fiscal_position_id or order[0].partner_id.property_account_position_id
        taxes = fpos.map_tax(line.product_id.taxes_id)
        price = -line.amount
        if order[0].expense_policy == 'time material':
            product = line.product_id.with_context(
                partner_id = order[0].partner_id.id,
                date_order = order[0].date_order,
                pricelist_id = order[0].pricelist_id.id,
                uom = line.product_uom_id.id
            )
            price = product.price

        sol = sol_obj.create({
            'order_id': order[0].id,
            'name': line.name,
            'sequence': last_sequence,
            'price_unit': price,
            'tax_id': [x.id for x in taxes],
            'discount': 0.0,
            'product_id': line.product_id.id,
            'product_uom': line.product_uom_id.id,
            'product_uom_qty': 0.0,
            'qty_delivered': line.unit_amount,
        })
        line.so_line = sol[0].id
        return line

