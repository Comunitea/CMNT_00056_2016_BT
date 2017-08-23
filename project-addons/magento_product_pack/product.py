# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api, exceptions, _
from openerp.addons.magentoerpconnect_product_tax.models.product import TaxProductImportMapper
from openerp.addons.magentoerpconnect.backend import magento
from openerp.addons.connector.unit.mapper import mapping


class MagentoProductProduct(models.Model):
    _inherit = 'magento.product.product'

    @api.model
    def product_type_get(self):
        res = super(MagentoProductProduct, self).product_type_get()
        res.append(('bundle', 'Bundle Product'))
        return res


@magento(replacing=TaxProductImportMapper)
class ProductPackMapper(TaxProductImportMapper):

    @mapping
    def pack_line_ids(self, record):
        pack_components = [(5,)]
        if record['type_id'] == 'bundle':
            binder = self.binder_for('magento.product.product')
            for component in record['_bundle_data']['options'][0]['selections']:
                mag_product_id = component['product_id']
                component_product = binder.to_openerp(mag_product_id,
                                                      unwrap=True)
                if not component_product:
                    raise exceptions.Warning(
                        _('Import error'),
                        _('Product not imported %s') % component['sku'])
                quantity = float(component['selection_qty'])
                pack_components.append((0, 0,
                                        {'product_id': component_product,
                                         'quantity': quantity}))
        product = self.env['product.product'].search(
            [('default_code', '=', record['sku']), '|',
             ('active', '=', False), ('active', '=', True)], order='active desc', limit=1)
        if not product:
            return {'pack_line_ids': pack_components}
        else:
            return {}

    @mapping
    def type(self, record):
        if record['type_id'] == 'bundle':
            return {'type': 'consu'}
        return super(ProductPackMapper, self).type(record)
