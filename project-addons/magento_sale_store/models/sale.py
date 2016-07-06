# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
from openerp.addons.magentoerpconnect.sale import SaleOrderImportMapper
from openerp.addons.magentoerpconnect.backend import magento
from openerp.addons.connector.unit.mapper import mapping


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    sale_store_id = fields.Many2one('sale.store', 'Store')

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


class SaleStore(models.Model):

    _name = 'sale.store'

    name = fields.Char(required=True)
    journal_id = fields.Many2one('account.journal', 'Journal')
    active = fields.Boolean("Active", default=True)
    logo = fields.Binary()


@magento(replacing=SaleOrderImportMapper)
class SaleOrderStoreImportMapper(SaleOrderImportMapper):

    @mapping
    def store_id(self, record):
        binder = self.binder_for('magento.store')
        magento_store = binder.to_openerp(record['store_id'])
        sale_store = self.env['magento.store'].browse(magento_store).store_id
        return {'sale_store_id': sale_store.id}
