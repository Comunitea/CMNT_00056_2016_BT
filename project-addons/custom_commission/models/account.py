# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def compute_commissions(self):
        for invoice in self:
            partner = invoice.partner_id.commercial_partner_id
            for line in invoice.invoice_line:
                agents = []
                if line.agents:
                    line.agents.unlink()
                if not line.commission_free:
                    for agent in partner.agents:
                        if not line.product_id:
                            commission = agent.plan.get_product_commission()
                        else:
                            commission = agent.plan.\
                                get_product_commission(product=
                                                       line.product_id.id)
                        if commission:
                            vals = {
                                'agent': agent.id,
                                'commission': commission.id,
                            }
                            agents.append(vals)
                    vals = [(0, 0, x) for x in agents]
                    line.write({'agents': vals})


class AccountInvoiceLine(models.Model):

    _inherit = "account.invoice.line"

    @api.multi
    def product_id_change(
            self, product, uom_id, qty=0, name='',
            type='out_invoice', partner_id=False, fposition_id=False,
            price_unit=False, currency_id=False, company_id=None):

        res = super(AccountInvoiceLine, self).product_id_change(
            product, uom_id, qty, name, type, partner_id,
            fposition_id, price_unit, currency_id, company_id)

        if self.ids and self.agents and res['value'].get('agents'):
            del res['value']['agents']

        return res
