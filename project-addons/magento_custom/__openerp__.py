# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "magento Customizations",
    "summary": "Debido a que no se puede heredar dos veces la misma clase del conector se meten todos los cambios conflictivos en este modulo",
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
        "connector_payment_method_code"
    ],
    "data": [
        'views/magento_store_view.xml',
        'views/sale.xml'
    ],
}
