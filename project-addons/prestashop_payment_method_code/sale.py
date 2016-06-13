# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.prestashoperpconnect.unit.mapper import SaleOrderMapper
from openerp.addons.connector.unit.mapper import mapping


@prestashop(replacing=SaleOrderMapper)
class SaleOrderMapperPaymenCode(SaleOrderMapper):

    @mapping
    def payment(self, record):
        methods = self.session.env['payment.method.code'].search(
            [
                ('code', '=', record['payment']),
                ('connector', '=', 'prestashop')
            ]
        )
        assert methods, ("Payment method '%s' has not been found ; "
                            "you should create it manually (in Sales->"
                            "Configuration->Sales->Payment Methods" %
                            record['payment'])
        method_id = methods[0].payment_method_id.id
        return {'payment_method_id': method_id}
