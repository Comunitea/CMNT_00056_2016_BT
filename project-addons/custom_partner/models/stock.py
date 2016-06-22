# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class StockQuant(models.Model):

    _inherit = "stock.quant"

    @api.model
    def quants_reconcile_negative(self, quant, move):
        quant = self.env["stock.quant"].browse(quant)
        move = self.env["stock.move"].browse(move)
        self._quant_reconcile_negative(quant, move)
        return True
