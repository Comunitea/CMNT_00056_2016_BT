# -*- coding: utf-8 -*-
# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
from openerp.addons.carrier_send_shipment.tools import unaccent, unspaces
from datetime import datetime, date
from base64 import decodestring
import logging
import tempfile

logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def send_tipsa(self, carrier_api):
        """
        Send shipments out to tipsa
        :param api: obj
        Return references, labels, errors
        """
        if self._context.get("from_barcode"):
            self = self.with_context(lang=self.env.user.lang)
        references = []
        labels = []

        default_service = carrier_api.get_default_carrier_service()
        for picking in self:
            service = (
                picking.carrier_service
                or picking.carrier_id.service
                or default_service
            )
            if not service:
                raise exceptions.Warning(
                    _("Api service error"),
                    _("Select a service or default service in tipsa API"),
                )

            notes = ""
            if picking.carrier_notes:
                notes = "%s\n" % picking.carrier_notes

            packages = picking.number_of_packages
            if not packages:
                packages = 1
            company_partner = (
                self.picking_type_id.warehouse_id.partner_id
                or self.company_id.partner_id
            )
            data = {
                "remitente_nombre": company_partner.name,
                "RecogidaDireccion": company_partner.street,
                "RecogidaCodigoPostal": company_partner.zip,
                "RecogidaPais": company_partner.country_id.name,
                "RecogidaPoblacion": company_partner.city,
                "RecogidaTelefono": company_partner.phone,
                "RecogidaEmail": company_partner.email,
                "RecogidaObservacion": notes,
                "RecogidaCodigoTipoServicio": service.code,
                "RecogidaFecha": datetime.now().strftime("%Y/%m/%d"),
                "destinatario_nombre": picking.partner_id.name,
                "EntregaDireccion": picking.partner_id.street,
                "EntregaCodigoPostal": picking.partner_id.zip,
                "EntregaPais": picking.partner_id.country_id.name,
                "EntregaPoblacion": picking.partner_id.city,
                "EntregaTelefono": picking.partner_id.phone,
                "EntregaEmail": picking.partner_id.email,
                "EntregaMovil": picking.partner_id.mobile,
                "total_bultos": packages,
                "total_peso": picking.weight_edit,
            }
            data["reembolso"] = ""
            data["valor_reembolso"] = ""
            price = None
            if picking.cash_on_delivery:
                price = picking.amount_total
                if not price:
                    raise exceptions.Warning(
                        _("Picking error"),
                        _(
                            'Shipment "%s" not have price and send cashondelivery'
                        )
                        % picking.name,
                    )
            if self.cash_on_delivery and price:
                data["reembolso"] = price
            reference = carrier_api.send_picking_tipsa(data)
            picking.write(
                {
                    "carrier_tracking_ref": reference,
                    "carrier_service": service.id,
                    "carrier_delivery": True,
                    "carrier_send_date": datetime.now(),
                    "carrier_send_employee": self.env.user.employee_ids
                    and self.env.user.employee_ids[0].id
                    or False,
                }
            )
            logger.info("Send Picking %s" % (picking.name))
            references.append(picking.name)

            labels += picking.print_labels_tipsa(carrier_api)
        return references, labels

    @api.multi
    def print_labels_tipsa(self, carrier_api):

        labels = []
        dbname = self.env.cr.dbname

        for picking in self:
            reference = picking.carrier_tracking_ref
            if not reference:
                logger.error(
                    "Picking %s has not been sent by tipsa." % (picking.name)
                )
                continue

            vals = {"picking_ref": reference}

            label = carrier_api.label_tipsa(vals)
            if not label:
                logger.error(
                    "Label for picking %s is not available from tipsa."
                    % picking.name
                )
                continue
            with tempfile.NamedTemporaryFile(
                prefix="%s-tipsa-%s-" % (dbname, reference),
                suffix=".pdf",
                delete=False,
            ) as temp:
                temp.write(decodestring(label))  # tipsa PDF file
            logger.info("Generated tmp label %s" % (temp.name))
            temp.close()
            labels.append(temp.name)
        picking.write({"carrier_printed": True})

        return labels
