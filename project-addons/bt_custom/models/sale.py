# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.onchange('payment_method_id')
    def onchange_payment_method_id_set_payment_term(self):
        res = super(SaleOrder,
                    self).onchange_payment_method_id_set_payment_term()
        if self.payment_method_id and self.payment_method_id.payment_mode_id:
            self.payment_mode_id = self.payment_method_id.payment_mode_id.id


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    takes = fields.Float()
    takes_change_flag = fields.Boolean()

    @api.multi
    def product_id_change(
        self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False,
            fiscal_position=False, flag=False):
        if not uom and self.env.context.get('orig_uom', False):
            uom = self.env.context['orig_uom']
        res = super(SaleOrderLine, self).product_id_change(
            pricelist, product, qty, uom, qty_uos, uos, name, partner_id, lang,
            update_tax, date_order, packaging, fiscal_position, flag)
        if not res['value']:
            return res
        product = res['value'].get('product_id', False) or product
        uom = res['value'].get('product_uom', False) or uom
        qty = res['value'].get('product_uom_qty', False) or qty
        if product and not self.env.context.get('updated_takes', False):
            product_obj = self.env['product.product'].browse(product)
            prod_uom_qty = self.env['product.uom']._compute_qty(
                uom, qty, product_obj.uom_id.id)
            res['value']['takes'] = product_obj.takes * prod_uom_qty
            res['value']['takes_change_flag'] = True
        return res

    @api.multi
    def onchange_product_uom(self, pricelist, product, qty=0, uom=False,
                             qty_uos=0, uos=False, name='', partner_id=False,
                             lang=False, update_tax=True, date_order=False,
                             fiscal_position=False):
        res = super(SaleOrderLine, self).onchange_product_uom(
            pricelist, product, qty, uom, qty_uos, uos, name, partner_id, lang,
            update_tax, date_order, fiscal_position)
        if not res['value']:
            return res
        product = res['value'].get('product_id', False) or product
        uom = res['value'].get('product_uom', False) or uom
        qty = res['value'].get('product_uom_qty', False) or qty
        if product and not self.env.context.get('updated_takes', False):
            product_obj = self.env['product.product'].browse(product)
            prod_uom_qty = self.env['product.uom']._compute_qty(
                uom, qty, product_obj.uom_id.id)
            res['value']['takes'] = product_obj.takes * prod_uom_qty
            res['value']['takes_change_flag'] = True
        return res

    @api.onchange('takes')
    def onchange_takes(self):
        if self.takes_change_flag:
            self.takes_change_flag = False
            return
        if self.product_id.takes:
            prod_uom_qty = self.takes / self.product_id.takes
            self.product_uom_qty = self.env['product.uom']._compute_qty(
                self.product_id.uom_id.id, prod_uom_qty, self.product_uom.id)
