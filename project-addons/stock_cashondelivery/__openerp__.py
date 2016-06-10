# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Cash on delivery management",
    "summary": "",
    "version": "8.0.1.0.0",
    "category": "Uncategorized",
    "website": "comunitea.com",
    "author": "Comunitea",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "sale",
        "stock",
        "sale_stock",
        "account_payment",
        "account_payment_sale",
        "stock_picking_valued"
    ],
    "data": [
        "views/account.xml",
        "views/stock.xml"
    ],
}
