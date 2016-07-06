# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    sale_store_id = fields.Many2one('sale.store', 'Store')
