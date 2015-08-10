# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, api, fields, exceptions
from openerp.tools.translate import _

class Company(models.Model):
    _inherit = 'res.company'
    timesheet_uom_id = fields.Many2one('product.uom', 'Timesheet UoM')

class product_template(models.Model):
    _inherit = 'product.template'
    is_timesheet = fields.Boolean(string="Track Service Time")

    @api.onchange('type', 'invoice_policy')
    def onchange_type(self):
        if self.type=='service' and self.invoice_policy=='time material':
            self.is_timesheet = True
        if self.type<>'service':
            self.is_timesheet = False
        return {}

class account_analytic_line(models.Model):
    _inherit = 'account.analytic.line'
    is_timesheet = fields.Boolean(string="Is a Timesheet")

class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'
    use_timesheets = fields.Boolean('Timesheets', help="Check this field if this project manages timesheets", deprecated=True)

