# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.addons.magentoerpconnect.sale import SaleOrderImportMapper
from openerp.addons.magentoerpconnect.backend import magento
from openerp.addons.connector.unit.mapper import mapping


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    sale_store_id = fields.Many2one('sale.store', 'Store', readonly=True,
                                    states={'draft': [('readonly', False)]})

    @api.model
    def _prepare_invoice(self, order, lines):
        res = super(SaleOrder, self)._prepare_invoice(order, lines)
        if order.sale_store_id:
            journal = order.sale_store_id.journal_id
            res['journal_id'] = journal.id
            res['sale_store_id'] = order.sale_store_id.id
        return res

    @api.multi
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        for obj in self:
            for picking in obj.picking_ids:
                picking.sale_store_id = obj.sale_store_id
        return res

    @api.multi
    def onchange_partner_id(self, part):
        res = super(SaleOrder, self).onchange_partner_id(part)
        if part and self.env.context.get('store_id', False):
            store_id = self.env.context['store_id']
            store = self.env['sale.store'].browse(store_id)
            partner = self.env['res.partner'].browse(part)
            payment_mode_id = partner.get_store_value(store, 'payment.mode')
            pricelist_id = partner.get_store_value(store, 'product.pricelist')
            payment_term = partner.get_store_value(
                store, 'account.payment.term')
            if payment_mode_id:
                res['value']['payment_mode_id'] = payment_mode_id
            if pricelist_id:
                res['value']['pricelist_id'] = pricelist_id
            if payment_term:
                res['value']['payment_term'] = payment_term
        return res

    @api.onchange('sale_store_id')
    def onchange_sale_store_id(self):
        if self.partner_id and self.sale_store_id:
            payment_mode_id = self.partner_id.get_store_value(
                self.sale_store_id, 'payment.mode')
            pricelist_id = self.partner_id.get_store_value(self.sale_store_id,
                                                           'product.pricelist')
            payment_term = self.partner_id.get_store_value(
                self.sale_store_id, 'account.payment.term')
            if payment_mode_id:
                self.payment_mode_id = payment_mode_id
            if pricelist_id:
                self.pricelist_id = pricelist_id
            if payment_term:
                self.payment_term = payment_term


class SaleStore(models.Model):

    _name = 'sale.store'

    name = fields.Char(required=True)
    journal_id = fields.Many2one('account.journal', 'Journal')
    active = fields.Boolean("Active", default=True)
    logo = fields.Binary()
    default_account_id = fields.Many2one('account.account', 'Default account for ecommerce customers importations')

    @api.multi
    def action_view_config(self):
        return {
            'domain': "[('store','='," + str(self.id) + ")]",
            'name': _('Store configuration'),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'sale.store.config',
            'type': 'ir.actions.act_window',
        }


class SaleStoreConfig(models.Model):

    _name = 'sale.store.config'

    partner = fields.Many2one('res.partner')
    store = fields.Many2one('sale.store')
    value = fields.Reference(
        [('product.pricelist', 'Pricelist'),
         ('payment.mode', 'Payment mode'),
         ('account.payment.term', 'Payment term')])


@magento(replacing=SaleOrderImportMapper)
class SaleOrderStoreImportMapper(SaleOrderImportMapper):

    @mapping
    def store_id(self, record):
        binder = self.binder_for('magento.store')
        magento_store = binder.to_openerp(record['store_id'])
        sale_store = self.env['magento.store'].browse(magento_store).store_id
        return {'sale_store_id': sale_store.id}
