# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class SaleOrder(models.Model):

    _inherit = "sale.order"

    carrier_service_id = fields.Many2one("carrier.api.service", "Carrier service")
    ship_return = fields.Boolean("Asm return")
    carrier_notes = fields.Text("Carrier notes")
    internal_notes = fields.Text("Internal notes")
    medical_code = fields.Char(
        "Medical code",
        readonly=True,
        related="partner_id.commercial_partner_id.medical_code",
    )

    @api.multi
    def onchange_partner_id(self, part):
        res = super(SaleOrder, self).onchange_partner_id(part)
        values = {}
        if part:
            partner = self.env["res.partner"].browse(part)
            values["ship_return"] = partner.ship_return
            if partner.carrier_service_id:
                values["carrier_service_id"] = partner.carrier_service_id.id
            values["carrier_notes"] = partner.carrier_notes
            res["value"].update(values)
        return res

    @api.multi
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        for order in self:
            order.picking_ids.write(
                {
                    "carrier_service": order.carrier_service_id.id,
                    "ship_return": order.ship_return,
                    "carrier_notes": order.carrier_notes,
                    "note": order.internal_notes,
                }
            )
        return res

    @api.onchange("carrier_id")
    def onchange_carrier_id(self):
        if self.carrier_id and not self.partner_id.carrier_service_id:
            self.carrier_service_id = self.carrier_id.service.id
        else:
            self.carrier_service_id = self.partner_id.carrier_service_id.id
