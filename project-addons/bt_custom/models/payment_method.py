# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class PaymentMethod(models.Model):

    _inherit = "payment.method"

    payment_mode_id = fields.Many2one("payment.mode", "Payment mode")
