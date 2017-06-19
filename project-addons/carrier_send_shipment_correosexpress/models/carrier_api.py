# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
import logging

try:
    from correosexpress.api import API as correosexpress_api
except ImportError:
    logger = logging.getLogger(__name__)
    message = 'Install correosexpress from Pypi: pip install asm'
    logger.error(message)
    raise Exception(message)


class CarrierApi(models.Model):
    _inherit = 'carrier.api'

    method = fields.Selection(selection_add=[('correosexpress', 'Correos express')])
    solicitante = fields.Char()
    insurance = fields.Float()
    cod_rte = fields.Char('Código remitente')

    @api.multi
    def test_correosexpress(self):
        '''
        Test Correos express connection
        '''
        raise NotImplementedError
