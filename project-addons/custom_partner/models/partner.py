# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ResPartner(models.Model):

    _inherit = 'res.partner'

    timetable = fields.Text("Timetable")
    medical_code = fields.Char("Medical code", size=32)
    carrier_service_id = fields.Many2one("carrier.api.service",
                                         "Carrier service")
    asm_return = fields.Boolean("Asm return")
    carrier_notes = fields.Text("Carrier notes")
