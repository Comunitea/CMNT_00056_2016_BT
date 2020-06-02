# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    def product_id_change(
        self,
        cr,
        uid,
        ids,
        pricelist,
        product,
        qty=0,
        uom=False,
        qty_uos=0,
        uos=False,
        name="",
        partner_id=False,
        lang=False,
        update_tax=True,
        date_order=False,
        packaging=False,
        fiscal_position=False,
        flag=False,
        context=None,
    ):
        res = super(SaleOrderLine, self).product_id_change(
            cr,
            uid,
            ids,
            pricelist,
            product,
            qty=qty,
            uom=uom,
            qty_uos=qty_uos,
            uos=uos,
            name=name,
            partner_id=partner_id,
            lang=lang,
            update_tax=update_tax,
            date_order=date_order,
            packaging=packaging,
            fiscal_position=fiscal_position,
            flag=flag,
            context=context,
        )
        product_obj = self.pool.get("product.product")
        if product and res.get("value") and res["value"].get("name"):
            context_partner = context.copy()
            partner = self.pool.get("res.partner").browse(cr, uid, partner_id, context)
            context_partner.update({"lang": partner.lang, "partner_id": partner_id})
            product_obj = product_obj.browse(cr, uid, product, context=context_partner)
            res["value"]["name"] = product_obj.name
        return res
