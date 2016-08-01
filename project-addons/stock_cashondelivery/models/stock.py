# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class StockPicking(models.Model):

    _inherit = 'stock.picking'
    cash_on_delivery = fields.Boolean(
        'Cash on delivery', related='sale_id.payment_mode_id.cash_on_delivery', readonly=True)
