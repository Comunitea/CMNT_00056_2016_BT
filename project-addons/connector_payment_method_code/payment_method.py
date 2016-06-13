# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class PaymentMethodCode(models.Model):

    _name = 'payment.method.code'

    payment_method_id = fields.Many2one('payment.method', 'Payment method')
    code = fields.Char()
    connector = fields.Selection([])


class PaymentMethod(models.Model):

    _inherit = 'payment.method'

    connector_codes  = fields.One2many('payment.method.code', 'payment_method_id')
