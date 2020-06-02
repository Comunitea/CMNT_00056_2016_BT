# -*- coding: utf-8 -*-
# © 2013 Zikzakmedia SL.
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Carrier api",
    "summary": "",
    "version": "8.0.1.0.0",
    "category": "Uncategorized",
    "website": "comunitea.com",
    "author": "Zikzakmedia SL, Comunitea",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["base", "delivery", "sale_store"],
    "data": [
        "views/carrier_api.xml",
        "views/delivery_carrier.xml",
        "security/ir.model.access.csv",
    ],
}
