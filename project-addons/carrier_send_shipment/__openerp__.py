# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Carrier send shipment",
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
        "delivery",
        "carrier_api",
        "stock",
        "hr",
        "stock_cashondelivery"
    ],
    "data": [
        'views/stock.xml',
        'views/assets.xml',
        'wizard/send_shipment_view.xml',
        'wizard/carrier_print.xml',
        'wizard/get_label.xml'
    ],
    'qweb': ['static/src/xml/picking.xml'],
}
