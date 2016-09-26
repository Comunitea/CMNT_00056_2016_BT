# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.magentoerpconnect.sale import SaleOrderImportMapper
from openerp.addons.magentoerpconnect.backend import magento
from openerp.addons.connector.unit.mapper import mapping


@magento(replacing=SaleOrderImportMapper)
class SaleOrderStoreImportMapper(SaleOrderImportMapper):

    @mapping
    def store_id(self, record):
        binder = self.binder_for('magento.store')
        magento_store = binder.to_openerp(record['store_id'])
        sale_store = self.env['magento.store'].browse(magento_store).store_id
        return {'sale_store_id': sale_store.id}
