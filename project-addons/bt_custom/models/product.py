# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class ProductProduct(models.Model):

    _inherit = 'product.product'

    ean14 = fields.Char('Code EAN14', size=14)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(ProductProduct, self).name_search(name, args=args, operator=operator, limit=limit)
        if not res:
            prods = self.search([('ean14', operator,name)]+ args, limit=limit)
            res = prods.name_get()
        return res
