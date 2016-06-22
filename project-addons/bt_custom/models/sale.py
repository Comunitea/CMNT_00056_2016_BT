# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.onchange('payment_method_id')
    def onchange_payment_method_id_set_payment_term(self):
        res = super(SaleOrder, self).onchange_payment_method_id_set_payment_term()
        if self.payment_method_id and self.payment_method_id.payment_mode_id:
            self.payment_mode_id = self.payment_method_id.payment_mode_id.id
