# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
from correosexpress.api import API as correosexpress_api


class CarrierApi(models.Model):
    _inherit = "carrier.api"

    method = fields.Selection(selection_add=[("correosexpress", "Correos express")])
    solicitante = fields.Char()
    insurance = fields.Float()
    cod_rte = fields.Char("Código remitente")

    @api.multi
    def test_correosexpress(self):
        """
        Test Correos express connection
        """
        self.ensure_one()
        message = "Connection unknown result"
        message = correosexpress_api(
            self.username, self.password, self.debug
        ).test_connection()
        raise exceptions.Warning(_("Connection test"), message)
