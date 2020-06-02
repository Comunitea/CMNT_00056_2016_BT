# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
import base64
import tempfile
import tarfile


class CarrierSendShipment(models.TransientModel):
    _name = "carrier.send.shipment"

    labels = fields.Binary("Labels", filename="file_name")
    sended = fields.Boolean()
    file_name = fields.Text("File Name")

    @api.multi
    def action_send(self):

        dbname = self.env.cr.dbname
        references = []
        labels = []

        pickings = self.env["stock.picking"].search(
            [("id", "in", self.env.context["active_ids"])]
        )
        for picking in pickings:
            refs, labs = picking.send_shipment_api()
            references += refs
            labels += labs

        #  Save file label in labels field
        if len(labels) == 1:  # A label generate simple file
            carrier_labels = base64.b64encode(open(labels[0], "rb").read())
            file_name = labels[0].split("/")[2]
        elif len(labels) > 1:  # Multiple labels generate tgz
            temp = tempfile.NamedTemporaryFile(
                prefix="%s-carrier-" % dbname, delete=False
            )
            temp.close()
            with tarfile.open(temp.name, "w:gz") as tar:
                for path_label in labels:
                    tar.add(path_label)
            tar.close()
            carrier_labels = base64.b64encode(open(temp.name, "rb").read())
            file_name = "%s.tgz" % temp.name.split("/")[2]
        else:
            carrier_labels = None
            file_name = None
        self.labels = carrier_labels
        self.file_name = file_name
        self.sended = True

        return {
            "context": self.env.context,
            "view_type": "form",
            "view_mode": "form",
            "res_model": "carrier.send.shipment",
            "res_id": self.id,
            "view_id": False,
            "type": "ir.actions.act_window",
            "target": "new",
        }

    @api.model
    def default_get(self, field_list):

        methods = []
        default = {}

        pickings = self.env["stock.picking"].browse(self._context.get("active_ids", []))
        for picking in pickings:
            if picking.state != "done" and not self._context.get("from_barcode", False):
                raise exceptions.Warning(
                    _("Picking state"), _("The picking %s is not in done state")
                )
            if picking.carrier_tracking_ref:
                raise exceptions.Warning(_("Shipment error"), _("Picking was sended"))
            carrier = picking.carrier_id.name
            apis = self.env["carrier.api"].search(
                [("carriers", "in", [picking.carrier_id.id])], limit=1
            )
            if not apis:
                raise exceptions.Warning(
                    _("Carrier error"), _("Carrier not have a api.")
                )
            api = apis and apis[0] or False
            if api.zips:
                zips = api.zips.split(",")
                if picking.partner_id.zip and picking.partner_id.zip in zips:
                    raise exceptions.Warning(
                        _(""),
                        _("Shipment %s not available to send zip %s")
                        % (picking.code, picking.partner_id.zip),
                    )

            if not api.method in methods:
                methods.append(api.method)

        if len(methods) > 1:
            raise exceptions.Warning(
                _("Carrier error"), _("Select only pickings of the same carrier")
            )
        return super(CarrierSendShipment, self).default_get(field_list)
