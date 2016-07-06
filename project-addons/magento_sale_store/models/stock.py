# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    sale_store_id = fields.Many2one('sale.store', 'Store')

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        res = super(StockPicking, self)._get_invoice_vals(key, inv_type,
                                                          journal_id, move)
        if move.picking_id.sale_store_id:
            journal = move.picking_id.sale_store_id.journal_id
            res['journal_id'] = journal.id
            res['sale_store_id'] = move.picking_id.sale_store_id.id
        return res
