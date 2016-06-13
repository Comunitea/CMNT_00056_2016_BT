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
        return res


class SaleStore(models.Model):

    _name = 'sale.store'

    name = fields.Char()
    journal_id = fields.Many2one('account.journal', 'Journal')


@magento(replacing=SaleOrderImportMapper)
class SaleOrderStoreImportMapper(SaleOrderImportMapper):

    @mapping
    def store_id(self, record):
        binder = self.binder_for('magento.store')
        magento_store = binder.to_openerp(record['store_id'])
        sale_store = self.env['magento.store'].browse(magento_store).store_id
        return {'sale_store_id': sale_store.id}

    # Cambios de metodo de pago
    @mapping
    def payment(self, record):
        import ipdb; ipdb.set_trace()
        record_method = record['payment']['method']
        method = self.env['payment.method.code'].search(
            [['code', '=', record_method], ['connector', '=', 'magento']],
            limit=1,
        )
        assert method, ("method %s should exist because the import fails "
                        "in SaleOrderImporter._before_import when it is "
                        " missing" % record['payment']['method'])
        return {'payment_method_id': method.payment_method_id.id}
