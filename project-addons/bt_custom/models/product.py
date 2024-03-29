# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
from openerp.osv import osv, fields as fields_old_api


class ProductProduct(models.Model):

    _inherit = "product.product"

    ean14 = fields.Char("Code EAN14", size=14)
    takes = fields.Integer("Takes per unit")

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        res = super(ProductProduct, self).name_search(
            name, args=args, operator=operator, limit=limit
        )
        if not args:
            args = []
        if not res:
            prods = self.search([("ean14", operator, name)] + args, limit=limit)
            res = prods.name_get()
        return res

    @api.multi
    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        if "standard_price" in vals:
            for product in self:
                boms = (
                    self.env["mrp.bom.line"]
                    .search([("product_id", "=", product.id)])
                    .mapped("bom_id")
                )
                if boms:
                    boms.update_standard_price_production()
        return res


class ProductProductOldApi(osv.osv):
    _inherit = "product.product"

    def _product_available(self, cr, uid, ids, name, arg, context=None):
        res = super(ProductProductOldApi, self)._product_available(
            cr, uid, ids, name, arg, context
        )
        if context.get("skip_stock"):
            # Devolvemos una cantidad para evitar aviso de stock
            for key in res.keys():
                res[key] = {
                    "qty_available": 999999999999,
                    "virtual_available": 999999999999,
                    "incoming_qty": 999999999999,
                    "outgoing_qty": 0,
                }
        return res

    def _search_product_quantity(self, cr, uid, obj, name, domain, context):
        return super(ProductProductOldApi, self)._search_product_quantity(
            cr, uid, obj, name, domain, context
        )

    _columns = {
        "virtual_available": fields_old_api.function(
            _product_available,
            multi="qty_available",
            digits_compute=dp.get_precision("Product Unit of Measure"),
            fnct_search=_search_product_quantity,
            type="float",
            string="Forecast Quantity",
        ),
    }
