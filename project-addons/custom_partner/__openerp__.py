# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Custom fields in Partners",
    "summary": "",
    "version": "8.0.1.0.0",
    "category": "Uncategorized",
    "website": "http://www.comunitea.com",
    "author": "Comunitea",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "carrier_api",
        "account",
        "stock",
        "account",
        "l10n_es_partner"
    ],
    "data": [
        "views/partner_view.xml",
        "views/sale.xml",
        "views/invoice.xml"
    ],
}
