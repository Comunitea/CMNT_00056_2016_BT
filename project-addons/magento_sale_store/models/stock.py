# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


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


class StockInvoiceOnshiping(models.TransientModel):


    _inherit = "stock.invoice.onshipping"

    @api.model
    def view_init(self, fields_list):
        res = super(StockInvoiceOnshiping, self).view_init(fields_list)
        active_ids = self.env.context.get('active_ids',[])
        store_id = False
        for picking in self.env['stock.picking'].browse(active_ids):
            if not store_id:
                store_id = picking.sale_store_id.id
            if picking.sale_store_id.id != store_id:
                raise exceptions.Warning(
                    _('Picking error'),
                    _('cannot invoice together pickings with different store'))
