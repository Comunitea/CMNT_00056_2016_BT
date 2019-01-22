# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    life_date_date = fields.Date(compute='_compute_life_date_date', store=True)

    @api.depends('life_date')
    def _compute_life_date_date(self):
        for lot in self:
            if not lot.life_date:
                lot.life_date_date = None
                continue
            life_date_datetime = fields.Datetime.from_string(lot.life_date)
            lot.life_date_date = fields.Date.to_string(life_date_datetime.date())
