# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields
import openerp.addons.decimal_precision as dp


class Carrier(models.Model):
    _inherit = "delivery.carrier"
    service = fields.Many2one("carrier.api.service", "Service")
    normal_price = fields.Float(
        "Normal Price",
        digits=dp.get_precision("Product Price"),
        help="Keep empty if the pricing depends on the advanced "
        "pricing per destination",
    )
