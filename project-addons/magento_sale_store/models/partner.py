# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ResPartner(models.Model):

    _inherit = 'res.partner'

    store_values = fields.One2many('sale.store.config', 'partner',
                                   'Stores configuration')

    @api.multi
    def get_store_value(self, store, model):
        values = self.store_values.filtered(
            lambda r, st=store, md=model: r.store == st and r.value._name == md
            )
        if values:
            return values[0].value
        return False
