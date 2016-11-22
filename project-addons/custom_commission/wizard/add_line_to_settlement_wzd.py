# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class AddLineToSettlemetWzd(models.TransientModel):

    _name = "add.line.tosettlement.wzd"

    def _default_agent(self):
        settlement_obj = self.env["sale.commission.settlement"]
        settlement = settlement_obj.browse(self.env.context['active_id'])
        return settlement.agent.id

    agent_id = fields.Many2one("res.partner", "Agent", readonly=True,
                               default=_default_agent)
    agent_lines = fields.\
        Many2many(comodel_name='account.invoice.line.agent',
                  relation="sale_commission_add_line_tosettlement_rel",
                  column1='wizard_id', column2='settlement_line_id',
                  string="Settlement lines")

    @api.multi
    def add_lines_to_settlement(self):
        settlement_line_obj = self.env["sale.commission.settlement.line"]
        for wzd in self:
            for line in wzd.agent_lines:
                vals = {'settlement': self.env.context["active_id"],
                        'agent_line': [(6, 0, [line.id])]}
                settlement_line_obj.create(vals)
