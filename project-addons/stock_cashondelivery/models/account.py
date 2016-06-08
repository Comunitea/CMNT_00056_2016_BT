# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class PaymentMode(models.Model):

    _inherit = 'payment.mode'
    cash_on_delivery = fields.Boolean('Cash on delivery')
