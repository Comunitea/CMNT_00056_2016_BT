# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class Carrier(models.Model):
    _inherit = 'delivery.carrier'
    service = fields.Many2one('carrier.api.service', 'Service')
