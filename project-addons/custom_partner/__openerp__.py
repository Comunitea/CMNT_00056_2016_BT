# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Custom fields in Partners",
    "summary": "",
    "version": "8.0.2.0.0",
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
        "l10n_es_partner",
        "account_due_dates_str",
        "sale",
        "sale_commission",
    ],
    "data": [
        "views/partner_view.xml",
        "views/sale.xml",
        "views/invoice.xml",
        "views/purchase_view.xml",
    ],
}
