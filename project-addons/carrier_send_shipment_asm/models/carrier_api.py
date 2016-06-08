# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
import logging

try:
    from asm.api import API as asm_api
except ImportError:
    logger = logging.getLogger(__name__)
    message = 'Install ASM from Pypi: pip install asm'
    logger.error(message)
    raise Exception(message)

class CarrierApi(models.Model):
    _inherit = 'carrier.api'

    method = fields.Selection(selection_add=[('asm', 'ASM')])

    @api.multi
    def test_asm(self):
        '''
        Test ASM connection
        '''
        self.ensure_one()
        message = 'Connection unknown result'
        message = asm_api(self.username, self.debug).test_connection()
        raise exceptions.Warning(_('Connection test'), message)
