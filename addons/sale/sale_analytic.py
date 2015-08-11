# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from openerp import api, fields, models, _

from openerp.tools.translate import _


class SaleOrder(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _compute_analytic(self):
        print 'Compute Analytic', self
        lines = {}
        domain = [('so_line','in',self.mapped('id'))]
        data = self.env['account.analytic.line'].read_group(domain, 
            ['so_line', 'unit_amount', 'product_uom_id'], ['product_uom_id', 'so_line'], lazy=False)
        print data
        for d in data:
            if not d['product_uom_id']: continue
            line = self.browse(d['so_line'][0])
            lines.setdefault(line, 0.0)
            uom = self.env['product.uom'].browse(d['product_uom_id'][0])
            print line, uom, 'Is Object?'

            qty = self.env['product.uom']._compute_qty_obj( uom, d['unit_amount'], line.product_uom)
            lines[line] += qty
            print '***', qty, uom.name, line.name

        for line, qty in lines.items():
            line.qty_delivered = qty
        return True


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"
    so_line = fields.Many2one('sale.order.line', string='Sale Order Line')

    @api.multi
    def _update_timesheet_line(self):
        sol_obj = self.env['sale.order.line']
        so_obj = self.env['sale.order']
        for line in self:
            if line.so_line.order_id.project_id.id == line.account_id.id:
                continue
            if (line.amount > 0) or not line.product_id:
                continue
            if line.product_id.invoice_policy not in ('time material','expense','order'):
                continue
            if (line.product_id.invoice_policy == 'order') and (line.product_id.type in ('product', 'consu')):
                continue

            if line.product_id.invoice_policy in ('time material', 'order'):
                sol = sol_obj.search([('order_id.project_id','=',line.account_id.id),('state','=','sale'),('product_id','=',line.product_id.id)])
                if sol:
                    line.so_line = sol[0].id
                    continue

            if line.product_id.invoice_policy == 'order':
                continue

            order = so_obj.search([('project_id','=',line.account_id.id),('state','=','sale')])

            print [('order_id','=',order[0].id)]
            last_so_line = sol_obj.search([('order_id','=',order[0].id)], order='sequence desc', limit=1)
            last_sequence = 100
            if last_so_line:
                last_sequence = last_so_line.sequence + 1

            fpos = order[0].fiscal_position_id or order[0].partner_id.property_account_position_id
            taxes = fpos.map_tax(line.product_id.taxes_id)
            price = -line.amount
            if line.product_id.invoice_policy == 'time material':
                product = line.product_id.with_context(
                    partner = order[0].partner_id.id,
                    date_order = order[0].date_order,
                    pricelist = order[0].pricelist_id.id,
                    quantity = line.unit_amount,
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
        return True

    @api.multi
    def write(self, values):
        todo = self.mapped('so_line')
        result = super(AccountAnalyticLine, self).write(values)
        if ('so_line' not in values) and ('account_id' in values):
            self._update_timesheet_line()
        if 'so_line' in values:
            todo |= self.mapped('so_line')
        todo._compute_analytic()
        return True

    @api.model
    def create(self, values):
        line = super(AccountAnalyticLine, self).create(values)
        line._update_timesheet_line()
        line.mapped('so_line')._compute_analytic()
        return line

