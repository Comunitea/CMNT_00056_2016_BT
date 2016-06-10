# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, exceptions, _
from openerp.addons.prestashoperpconnect.unit.import_synchronizer import TemplateRecordImporter
from openerp.addons.prestashoperpconnect.product import TemplateMapper
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.connector.unit.mapper import mapping


@prestashop(replacing=TemplateRecordImporter)
class TemplatePackImporter(TemplateRecordImporter):

    def _after_import(self, erp_id):
        res = super(TemplatePackImporter, self)._after_import(erp_id)
        for variant in erp_id.product_variant_ids:
            variant.pack_line_ids.unlink()
            for pack_line in erp_id.imported_pack_line_ids:
                pack_variant = pack_line.product_id.product_variant_ids and pack_line.product_id.product_variant_ids[0]
                if not pack_variant:
                    continue
                self.env['product.pack.line'].create(
                    {'parent_product_id': variant.id,
                     'quantity': pack_line.quantity,
                     'product_id': pack_variant.id})
        return res


@prestashop(replacing=TemplateMapper)
class TemplatePackMapper(TemplateMapper):

    @mapping
    def imported_pack_line_ids(self, record):
        pack_components = [(5,)]
        if record['type']['value'] and record['type']['value'] == 'pack':
            binder = self.binder_for('prestashop.product.template')
            only_one = False
            for component in record['associations']['product_bundle']['product']:
                if  isinstance(record['associations']['product_bundle']['product'], dict):
                    # El pack solo contiene un producto.
                    only_one = True
                    component =  record['associations']['product_bundle']['product']
                presta_product_id = component['id']
                component_product = binder.to_openerp(presta_product_id,
                                                      unwrap=True)
                if not component_product:
                    raise exceptions.Warning(
                        _('Import error'),
                        _('Product not imported %s') % component['id'])
                quantity = float(component['quantity'])
                pack_components.append((0, 0,
                                        {'product_id': component_product,
                                         'quantity': quantity}))
                if only_one:
                    break
        return {'imported_pack_line_ids': pack_components}

    @mapping
    def type(self, record):
        if record['type']['value'] and record['type']['value'] == 'pack':
            return {'type': 'service'}
        return super(TemplatePackMapper, self).type(record)


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    imported_pack_line_ids = fields.One2many('imported.pack.line', 'template_id')

class ImportedPackLine(models.Model):

    _name = 'imported.pack.line'

    template_id = fields.Many2one('product.template')
    product_id = fields.Many2one('product.template')
    quantity = fields.Float()
