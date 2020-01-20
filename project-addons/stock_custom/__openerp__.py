# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Stock custom',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'sale_order_lot_selection',
        'stock_picking_valued'
    ],
    'data': [
        'views/sale.xml',
        'views/report_saleorder.xml',
        'views/stock_report.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
