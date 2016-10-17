# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    def do_print_invoice(self):
        if self.sale_id.invoice_ids:
            return self.sale_id.invoice_ids.invoice_print()
