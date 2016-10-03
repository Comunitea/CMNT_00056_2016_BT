# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.multi
    def invoice_validate(self):
        for inv in self:
            if inv.early_payment_discount:
                inv.button_compute_early_payment_disc()
        res = super(AccountInvoice, self).invoice_validate()
        return res
