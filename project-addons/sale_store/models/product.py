# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ProductProduct(models.Model):

    _inherit = "product.product"

    store_ids = fields.Many2many("sale.store", "sale_store_product_rel",
                                 "product_id", "store_id", string="Stores")
