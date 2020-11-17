# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "BT customizations",
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
        "stock",
        "sale_payment_method",
        "sale",
        "hr_holidays",
        "sale_early_payment_discount",
        "purchase",
        "account_payment_sale",
        "l10n_es_aeat_mod340",
        "l10n_es_account_invoice_sequence",
        "account_invoice_merge",
        "openerp_sale_promotions",
        "sale_store",
        "sale_display_stock",
        "sale_commission",
        "mrp"
    ],
    "data": [
        "data/res_groups.xml",
        "views/payment_method.xml",
        "views/product.xml",
        "views/sale.xml",
        "views/stock.xml",
        "views/report_autoinvoice.xml",
        "views/hr_holidays_view.xml",
        "wizard/account_invoice_mass_cancel_wizard.xml",
        "wizard/account_invoice_mass_draft_wizard.xml",
    ],
}
