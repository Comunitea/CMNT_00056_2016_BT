# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, exceptions, _
import base64
import tempfile
import tarfile

class CarrierGetLabel(models.TransientModel):

    _name = 'carrier.get.label'

    codes = fields.Char('Codes', required=True,
        help='Introduce codes or tracking reference of shipments separated by commas.')

    sended = fields.Boolean()
    labels = fields.Binary('Labels', filename='file_name')
    file_name = fields.Char('File Name')


    @api.multi
    def action_print(self):
        dbname = self.env.cr.dbname
        labels = []
        codes = [l.strip() for l in self.codes.split(',')]
        pickings = self.env['stock.picking'].search(
            [('state', '=', 'done'), '|',
             ('name', 'in', codes), ('carrier_tracking_ref', 'in', codes)])
        methods = []
        for picking in pickings:
            if not picking.carrier_tracking_ref:
                raise exceptions.Warning(_('Shipment error'), _('Picking %s was not sended') % picking.name)
            carrier = picking.carrier_id.name
            apis = self.env['carrier.api'].search([('carriers', 'in', [picking.carrier_id.id])], limit=1)
            api = apis and apis[0] or False

            if not api.method in methods:
                methods.append(api.method)

        if len(methods) > 1:
            raise exceptions.Warning(_('Carrier error'), _('Select only pickings of the same carrier'))

        for picking in pickings:
            apis = self.env['carrier.api'].search([('carriers', 'in', [picking.carrier_id.id])], limit=1)
            if not apis:
                continue
            api = apis[0]

            print_label = getattr(picking, 'print_labels_%s' % api.method)
            labs = print_label(api)

            labels += labs

        #  Save file label in labels field
        if len(labels) == 1:  # A label generate simple file
            carrier_labels =  base64.b64encode(open(labels[0], "rb").read())
            file_name = labels[0].split('/')[2]
        elif len(labels) > 1:  # Multiple labels generate tgz
            temp = tempfile.NamedTemporaryFile(prefix='%s-carrier-' % dbname,
                delete=False)
            temp.close()
            with tarfile.open(temp.name, "w:gz") as tar:
                for path_label in labels:
                    tar.add(path_label)
            tar.close()
            carrier_labels = base64.b64encode(open(temp.name, "rb").read())
            file_name = '%s.tgz' % temp.name.split('/')[2]
        else:
            carrier_labels = None
            file_name = None
        self.labels = carrier_labels
        self.file_name = file_name
        self.sended = True

        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'carrier.get.label',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
