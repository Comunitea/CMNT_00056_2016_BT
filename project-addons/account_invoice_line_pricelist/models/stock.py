# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        inv_vals = super(StockPicking, self)._get_invoice_vals(key, inv_type, journal_id, move)
        sale = move.picking_id.sale_id
        if sale and inv_type in ('out_invoice', 'out_refund'):
            inv_vals.update({
                'pricelist_id': sale.pricelist_id.id,
                })
        return inv_vals
