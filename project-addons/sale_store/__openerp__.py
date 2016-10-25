# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale store",
    "summary": "",
    "version": "8.0.1.0.0",
    "category": "Uncategorized",
    "website": "comunitea.com",
    "author": "Comunitea",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale_stock", "account_payment", "delivery",
        "account_payment_partner"
    ],
    "data": ['security/ir.model.access.csv',
             'views/layout.xml',
             'views/partner.xml',
             'views/sale.xml',
             'views/sale_store_view.xml',
             'views/stock.xml',
             'views/product.xml',
             'views/invoice.xml'],
}
