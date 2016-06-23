# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields
from openerp.addons.prestashoperpconnect.unit.mapper import ShopImportMapper
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.connector.unit.mapper import mapping

class PrestashopStore(models.Model):
    _inherit = 'prestashop.shop'

    store_id = fields.Many2one('sale.store', 'Store')


@prestashop(replacing=ShopImportMapper)
class ShopImportMapper_store(ShopImportMapper):

    @mapping
    def store_id(self, record):
        store_name = record['name']
        store = self.env['sale.store'].search([('name', '=', store_name)])
        if not store:
            store = self.env['sale.store'].create({'name': store_name})
        return {'sale_store_id': store.id}
