# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
from openerp.addons.magentoerpconnect.magento_model import StoreImportMapper
from openerp.addons.magentoerpconnect.backend import magento
from openerp.addons.connector.unit.mapper import mapping



class MagentoStore(models.Model):
    _inherit = 'magento.store'

    store_id = fields.Many2one('sale.store', 'Store')


@magento(replacing=StoreImportMapper)
class SaleStoreImportMapper(StoreImportMapper):

    @mapping
    def store_id(self, record):
        store_name = record['name']
        store = self.env['sale.store'].search([('name', '=', store_name)])
        if not store:
            store = self.env['sale.store'].create({'name': store_name})
        return {'sale_store_id': store.id}
