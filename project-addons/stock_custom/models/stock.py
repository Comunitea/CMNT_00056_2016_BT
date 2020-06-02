# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models
import pytz


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    use_date_date = fields.Date(compute="_compute_use_date_date", store=True)

    @api.depends("use_date")
    def _compute_use_date_date(self):
        for lot in self:
            if not lot.use_date:
                lot.use_date_date = None
                continue
            use_date_datetime = fields.Datetime.from_string(lot.use_date)
            tz_name = lot._context.get("tz") or lot.env.user.tz
            if tz_name:
                use_date_datetime_utc = pytz.timezone("UTC").localize(
                    use_date_datetime, is_dst=False
                )  # UTC = no DST
                use_date_tz = use_date_datetime_utc.astimezone(pytz.timezone(tz_name))
                lot.use_date_date = fields.Date.to_string(use_date_tz.date())
