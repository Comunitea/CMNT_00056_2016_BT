# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Commission customizations",
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
        "sale_commission_product_plan"
    ],
    "data": [
        "wizard/plan_add_category_wizard.xml",
        "views/sale_view.xml",
        "views/account.xml"
    ],
}
