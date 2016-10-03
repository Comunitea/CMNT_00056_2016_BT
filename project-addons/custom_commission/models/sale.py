# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.multi
    def compute_commissions(self):
        for sale in self:
            for line in sale.order_line:
                if line.agents:
                    line.agents.unlink()
                if not line.commission_free:
                    vals = line.with_context(partner_id=sale.partner_id.id).\
                        _default_agents()
                    line.write({'agents': vals})
