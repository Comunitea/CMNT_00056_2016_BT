# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, exceptions, _
import logging

try:
    from envialia.api import API
except ImportError:
    logger = logging.getLogger(__name__)
    message = "Install Envialia from Pypi: pip install envialia"
    logger.error(message)
    raise Exception(message)


class CarrierApi(models.Model):
    _inherit = "carrier.api"

    method = fields.Selection(selection_add=[("envialia", "Envialia")])
    envialia_agency = fields.Char("Agency", help="Envialia Agency")

    def test_envialia(self):
        """
        Test Envialia connection
        """
        self.ensure_one()
        message = "Connection unknown result"
        with API(
            self.envialia_agency, self.username, self.password, self.debug
        ) as envialia_api:
            message = envialia_api.test_connection()
            if message.get("error"):
                message = "connection_error"
            elif message.get("session"):
                message = "connection_successfully"
            else:
                message = "connection_error"
            raise exceptions.Warning(_("Connection test"), message)


class CarrierApiService(models.Model):
    _inherit = "carrier.api.service"

    envialia_saturday = fields.Boolean()
