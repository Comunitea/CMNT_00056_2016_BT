# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def compute_commissions(self):
        for invoice in self:
            for line in invoice.invoice_line:
                if line.agents:
                    line.agents.unlink()
                if not line.commission_free:
                    vals = line.with_context(partner_id=invoice.partner_id.id).\
                        _default_agents()
                    line.write({'agents': vals})
