# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, fields


class AccountJournal(models.Model):

    _inherit = "account.journal"

    autoinvoice = fields.Boolean("Autoinvoice")


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    autoinvoice = fields.Boolean("Autoinvoice", readonly=True,
                                 related="journal_id.autoinvoice")

    @api.multi
    def action_number(self):
        res = super(AccountInvoice, self).action_number()
        for inv in self:
            if inv.autoinvoice and inv.invoice_number and not inv.reference:
                inv.reference = inv.invoice_number
        return res

    @api.multi
    def action_move_create(self):
        for inv in self:
            if inv.early_payment_discount:
                inv.button_compute_early_payment_disc()
        res = super(AccountInvoice, self).action_move_create()
        return res
