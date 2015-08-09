# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields
from openerp.osv import osv
from openerp.tools.translate import _
from openerp.exceptions import UserError

class account_analytic_line(osv.osv):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'
    _columns = {
        'product_uom_id': fields.many2one('product.uom', 'Unit of Measure'),
        'product_id': fields.many2one('product.product', 'Product'),
        'general_account_id': fields.many2one('account.account', 'Financial Account', required=True, ondelete='restrict'),
        'move_id': fields.many2one('account.move.line', 'Move Line', ondelete='cascade', select=True),
        'code': fields.char('Code', size=8),
        'ref': fields.char('Ref.'),
        'currency_id': fields.related('move_id', 'currency_id', type='many2one', relation='res.currency', string='Account Currency', store=True, help="The related account currency if not equal to the company one.", readonly=True),
        'amount_currency': fields.related('move_id', 'amount_currency', type='float', string='Amount Currency', store=True, help="The amount expressed in the related account currency if not equal to the company one.", readonly=True),
    }

    _defaults = {
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.analytic.line', context=c),
    }
    _order = 'date desc'

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.get('from_date',False):
            args.append(['date', '>=', context['from_date']])
        if context.get('to_date',False):
            args.append(['date','<=', context['to_date']])
        return super(account_analytic_line, self).search(cr, uid, args, offset, limit,
                order, context=context, count=count)

    def _check_company(self, cr, uid, ids, context=None):
        lines = self.browse(cr, uid, ids, context=context)
        for l in lines:
            if l.move_id and not l.account_id.company_id.id == l.move_id.account_id.company_id.id:
                return False
        return True

    def view_header_get(self, cr, user, view_id, view_type, context=None):
        if context is None:
            context = {}
        if context.get('account_id', False):
            # account_id in context may also be pointing to an account.account.id
            cr.execute('select name from account_analytic_account where id=%s', (context['account_id'],))
            res = cr.fetchone()
            if res:
                res = _('Entries: ')+ (res[0] or '')
            return res
        return False


