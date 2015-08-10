# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from openerp.tools.translate import _
from openerp import api, fields, models, _
from openerp.addons.decimal_precision import decimal_precision as dp

class SaleOrder(models.Model):
    _inherit = "sale.order"
    expense_policy = fields.Selection([
            ('at cost', 'Charge expenses at cost'),
            ('price', 'Charge expenses based on price'),
            ('no', 'Do not charge expenses'),
        ], string='Expenses', default='no')

class HrExpense(models.Model):
    _inherit = "hr.expense.expense"
    @api.multi
    def expense_accept(self):
        result = super(HrExpense, self).expense_accept()
        sol_obj = self.env['sale.order.line']
        so_obj = self.env['sale.order']
        for expense in self:
            orders = self.env['sale.order']
            for line in expense.line_ids:
                order = sol_obj.search([('project_id', '=', line.analytic_account.id), ('state','=','sale'), ('expense_policy','<>','no')])
                if not len(order):
                    continue
                last_so_line = sol_obj.search([('order_id','=',order[0].id)], _order='sequence desc', limit=1)
                last_sequence = 100
                if last_so_line:
                    last_sequence = last_so_line.sequence + 1
                fpos = order[0].fiscal_position_id or order[0].partner_id.property_account_position_id
                taxes = fpos.map_tax(line.product_id.taxes_id)
                price = line.unit_amount
                if order[0].expense_policy == 'price':
                    product = line.product_id.with_context(
                        partner_id = order[0].partner_id.id,
                        date_order = order[0].date_order,
                        pricelist_id = order[0].pricelist_id.id,
                        uom = line.product_uom.id
                    )
                    price = product.price

                sol_obj.create({
                    'order_id': order[0].id,
                    'name': line.name
                    'sequence': last_sequence,
                    'price_unit': price,
                    'tax_id': [x.id for x in taxes],
                    'discount': 0.0,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom.id,
                    'product_uom_qty': line.unit_quantity,
                })
                orders |= order[0]
            if orders:
                msg = ", ".join(orders.mapped('name'))
                expense.message_post(body=_("Expenses added to orders: ") + msg)
            else:
                expense.message_post(body=_("None of these expenses will be charged to customers."))
        return result

