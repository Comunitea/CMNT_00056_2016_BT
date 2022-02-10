# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
from openerp.addons.connector.session import ConnectorSession

from openerp.addons.connector.queue.job import job


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.model
    def process_barcode_from_ui(self, picking_id, barcode_str, visible_op_ids):
        answer = super(StockPicking, self).process_barcode_from_ui(
            picking_id, barcode_str, visible_op_ids
        )
        product_obj = self.env["product.product"]
        stock_operation_obj = self.env["stock.pack.operation"]
        matching_product_ids = product_obj.search([("ean14", "=", barcode_str)])
        if matching_product_ids:
            op_id = stock_operation_obj._search_and_increment(
                picking_id,
                [("product_id", "=", matching_product_ids[0].id)],
                filter_visible=True,
                visible_op_ids=visible_op_ids,
                increment=True,
            )
            answer["operation_id"] = op_id
            return answer
        return answer

    def _prepare_values_extra_move(
        self, cr, uid, op, product, remaining_qty, context=None
    ):
        res = super(StockPicking, self)._prepare_values_extra_move(
            cr, uid, op, product, remaining_qty, context=context
        )
        if op.linked_move_operation_ids:
            res.update(
                {
                    "date_expected": op.linked_move_operation_ids[
                        -1
                    ].move_id.date_expected
                }
            )
        return res


class StockInventory(models.Model):

    _inherit = "stock.inventory"

    @api.multi
    def launch_action_done_job(self):

        session = ConnectorSession(
            self.env.cr,
            self.env.user.id,
            context=self.env.context,
        )
        for inv in self:
            action_done_job.delay(session, "stock.inventory", inv.id)


@job()
def action_done_job(session, model_name, inventory_id):
    model = session.env[model_name]
    inventory = model.browse(inventory_id)
    if inventory.exists():
        inventory.action_done()
