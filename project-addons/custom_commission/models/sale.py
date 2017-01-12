# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.multi
    def compute_commissions(self):
        for sale in self:
            partner = sale.partner_id.commercial_partner_id
            for line in sale.order_line:
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


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False):

        res = super(SaleOrderLine, self).product_id_change(
            pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
            name=name, partner_id=partner_id, lang=lang, update_tax=update_tax,
            date_order=date_order, packaging=packaging,
            fiscal_position=fiscal_position, flag=flag)

        if self.ids and self.agents and res['value'].get('agents'):
            del res['value']['agents']

        return res

    @api.multi
    def unlink(self):
        for line in self:
            if line.agents:
                line.agents.unlink()
        return super(SaleOrderLine, self).unlink()
