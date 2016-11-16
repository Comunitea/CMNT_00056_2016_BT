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
