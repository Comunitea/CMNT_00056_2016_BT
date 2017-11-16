# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def recalculate_prices(self):
        return self.reset_lines()

    @api.multi
    def reset_lines(self):
        for line in self.mapped('invoice_line'):
            res = line.with_context(
                pricelist_id=self.pricelist_id.id).product_id_change(
                    line.product_id.id, line.uos_id.id, line.quantity,
                    line.name, self.type, self.partner_id.id,
                    self.fiscal_position.id, line.price_unit,
                    self.currency_id.id, self.company_id.id)
            if 'value' in res and 'price_unit' in res['value']:
                line.write({'price_unit': res['value']['price_unit']})
        return True
