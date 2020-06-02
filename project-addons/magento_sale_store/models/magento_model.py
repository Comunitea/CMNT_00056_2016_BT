# -*- coding: utf-8 -*-
# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class MagentoBackend(models.Model):
    _inherit = "magento.backend"

    default_user_id = fields.Many2one("res.users", "Comercial por defecto")
