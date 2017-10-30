# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    sale_store_id = fields.Many2one('sale.store', 'Store')

    @api.multi
    def action_move_create(self):
        super_invoices = self.env['account.invoice']
        for invoice in self:
            if not self.sale_store_id or not self.sale_store_id.not_create_invoice_moves:
                super_invoices += invoice
        if self - super_invoices:
            for inv in self - super_invoices:
                if not inv.date_invoice:
                    ctx = dict(self._context, lang=inv.partner_id.lang)
                    inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
        if super_invoices:
            return super(AccountInvoice, super_invoices).action_move_create()
        return True

    @api.multi
    def action_number(self):
        super_invoices = self.env['account.invoice']
        for invoice in self:
            if not self.sale_store_id or not self.sale_store_id.not_create_invoice_moves:
                super_invoices += invoice
        if super_invoices:
            return super(AccountInvoice, super_invoices).action_number()
        if self - super_invoices:
            for inv in self - super_invoices:
                if not inv.invoice_number:
                    sequence = inv.journal_id.invoice_sequence_id
                    if sequence:
                        number = sequence.with_context({
                            'fiscalyear_id': inv.period_id.fiscalyear_id.id
                        }).next_by_id(sequence.id)
                    else:
                        # TODO: raise an error if the company is flagged
                        #       as requiring a separate numbering for invoices
                        number = False
                    inv.write({
                        'number': number,
                        'invoice_number': number
                    })
                else:
                    inv.write({
                        'number': inv.invoice_number,
                    })
                self.write({'internal_number': inv.number})

                if inv.type in ('in_invoice', 'in_refund'):
                    if not inv.reference:
                        ref = inv.number
                    else:
                        ref = inv.reference
                else:
                    ref = inv.number
        return True
