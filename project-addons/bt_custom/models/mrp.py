# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class MrpBom(models.Model):

    _inherit = "mrp.bom"

    @api.model
    def create(self, vals):
        res = super(MrpBom, self).create(vals)
        res.update_standard_price_production()
        return res

    @api.multi
    def write(self, vals):
        res = super(MrpBom, self).write(vals)
        self.update_standard_price_production()
        return res

    @api.multi
    def update_standard_price_production(self):
        for production in self:
            if production.product_tmpl_id.product_variant_ids:
                product = production.product_tmpl_id.product_variant_ids[0]
                cost_price = 0.0
                for bom_line in production.bom_line_ids:
                    bom_line_qty = self.env["product.uom"]._compute_qty_obj(
                        bom_line.product_uom,
                        bom_line.product_qty,
                        bom_line.product_id.uom_id,
                    )
                    cost_price += bom_line.product_id.standard_price * bom_line_qty

                production_product_qty = self.env["product.uom"]._compute_qty_obj(
                    production.product_uom, production.product_qty, product.uom_id
                )
                product.write({"standard_price": cost_price / production_product_qty})
        return True
