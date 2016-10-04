# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models


class MrpProduction(models.Model):

    _inherit = "mrp.production"

    _defaults = {'location_dest_id': False}
