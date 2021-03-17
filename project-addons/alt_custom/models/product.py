# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class ProductProduct(osv.osv):
    _inherit = 'product.product'

    def _product_available(self, cr, uid, ids, name, arg, context=None):
        res = super(ProductProduct, self)._product_available(cr, uid, ids, name, arg, context)
        if context.get('skip_stock'):
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
        return super(ProductProduct, self)._search_product_quantity(cr, uid, obj, name, domain, context)

    _columns = {
        'virtual_available': fields.function(_product_available, multi='qty_available', digits_compute=dp.get_precision('Product Unit of Measure'),
        fnct_search=_search_product_quantity, type='float', string='Forecast Quantity'),
    }
