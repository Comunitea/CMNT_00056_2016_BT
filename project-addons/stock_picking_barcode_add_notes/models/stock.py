# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.multi
    def do_print_invoice(self):
        if self.sale_id.invoice_ids and len(self.sale_id.invoice_ids) == 1:
            return self.sale_id.invoice_ids.invoice_print()
        elif not self.sale_id.invoice_ids:
            raise exceptions.Warning(_("Any invoice related to this picking"))
        else:
            raise exceptions.Warning(
                _(
                    "It was found more than one invoice "
                    "related to this picking, please "
                    "print your choice from backend"
                )
            )
