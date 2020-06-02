# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class AccountJournal(models.Model):

    _inherit = "account.journal"

    code = fields.Char(
        "Code", size=12, required=True, help="The code will be displayed on reports."
    )
