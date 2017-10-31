# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, exceptions, _


class AccountInvoiceMassCancelWizard(models.TransientModel):

    _name = 'account.invoice_mass_cancel_wizard'

    @api.multi
    def apply(self):
        self.ensure_one()
        invoices = self.env['account.invoice'].browse(self._context.get('active_ids', []))
        invoices.signal_workflow('invoice_cancel')
        return {'type': 'ir.actions.act_window_close'}
