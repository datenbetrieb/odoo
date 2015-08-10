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
        # if product used in timesheet: False
        self.qty_delivered_updateable = True

    @api.multi
    @api.depends('order_id.project_id.line_ids.unit_amount')
    def _get_delivered_qty(self):
        # Todo: compute this field
        self.qty_delivered = 0
