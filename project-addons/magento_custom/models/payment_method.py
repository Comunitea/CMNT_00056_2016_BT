# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class PaymentMethodCode(models.Model):

    _inherit = 'payment.method.code'

    connector = fields.Selection(selection_add=[('magento', 'Magento')])
