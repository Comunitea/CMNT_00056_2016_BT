# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "magento store",
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
        "magentoerpconnect",
    ],
    "data": [
        'views/magento_store_view.xml',
        'views/sale.xml',
        'views/prestashop_store_view.xml',
        'security/ir.model.access.csv',
        'views/sale_store_view.xml',
        'views/layout.xml'
    ],
}
