# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Reinvoice Expenses',
    'version': '1.1',
    'category': 'Sales Management',
    'description': """
Allow selling expenses
======================
""",
    'author': 'OpenERP S.A.',
    'website': 'https://www.odoo.com/',
    'depends': ['hr_expense','sale_contract'],
    'data': ['sale_expense_view.xml'],
    'demo': [],
    'installable': True,
    'auto_install': True,
}
