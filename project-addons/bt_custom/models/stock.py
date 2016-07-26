# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.model
    def process_barcode_from_ui(self, picking_id, barcode_str, visible_op_ids):
        answer = super(StockPicking, self).process_barcode_from_ui(
            picking_id, barcode_str, visible_op_ids)
        product_obj = self.env['product.product']
        stock_operation_obj = self.env['stock.pack.operation']
        matching_product_ids = product_obj.search(
            [('ean14', '=', barcode_str)])
        if matching_product_ids:
            op_id = stock_operation_obj._search_and_increment(
                picking_id, [('product_id', '=', matching_product_ids[0].id)],
                filter_visible=True, visible_op_ids=visible_op_ids,
                increment=True)
            answer['operation_id'] = op_id
            return answer
        return answer
