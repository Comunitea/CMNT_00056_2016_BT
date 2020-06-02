# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class AccountInvoiceLine(models.Model):

    _inherit = "account.invoice.line"

    @api.multi
    def product_id_change(
        self,
        product,
        uom_id,
        qty=0,
        name="",
        type="out_invoice",
        partner_id=False,
        fposition_id=False,
        price_unit=False,
        currency_id=False,
        company_id=None,
    ):
        res = super(AccountInvoiceLine, self).product_id_change(
            product,
            uom_id,
            qty=qty,
            name=name,
            type=type,
            partner_id=partner_id,
            fposition_id=fposition_id,
            price_unit=price_unit,
            currency_id=currency_id,
            company_id=company_id,
        )
        if product and res.get("value") and res["value"].get("name"):
            part = self.env["res.partner"].browse(partner_id)
            if part.lang:
                self = self.with_context(lang=part.lang)
            product_obj = self.env["product.product"].browse(product)
            res["value"]["name"] = product_obj.name
        return res
