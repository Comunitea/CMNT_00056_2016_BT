# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api


class AccountInvoiceMassDraftWizard(models.TransientModel):

    _name = 'account.invoice_mass_draft_wizard'

    @api.multi
    def apply(self):
        self.ensure_one()
        invoices = self.env['account.invoice'].\
            browse(self._context.get('active_ids', []))
        invoices.signal_workflow('action_cancel_draft')
        return {'type': 'ir.actions.act_window_close'}
