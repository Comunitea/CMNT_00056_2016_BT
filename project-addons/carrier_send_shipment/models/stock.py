# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
from datetime import datetime
import base64


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    asm_return = fields.Boolean(
        'ASM Return', states={'done': [('readonly', True)]},
        help='Active return when send API shipment')

    carrier_service = fields.Many2one('carrier.api.service',
        'Carrier API Service')
    carrier_delivery = fields.Boolean('Delivered', readonly=True,
        help='The package has been delivered', copy=False)
    carrier_printed = fields.Boolean('Printed', readonly=True,
        help='Picking is already printed', copy=False)
    carrier_notes = fields.Text('Carrier Notes',
        states={'done': [('readonly', True)]},
        help='Add notes when send API shipment')
    carrier_send_employee = fields.Many2one('hr.employee', readonly=True)
    carrier_send_date = fields.Datetime(readonly=True)
    weight_edit = fields.Float('Weight', compute='compute_weight', store=True,
                               readonly=False)
    weight_net_edit = fields.Float('Net weight', compute='compute_weight',
                                   store=True, readonly=False)

    @api.one
    @api.depends('weight', 'weight_net')
    def compute_weight(self):
        self.weight_edit = self.weight
        self.weight_net_edit = self.weight_net

    @api.onchange('carrier_id')
    def on_change_carrier(self):
        self.carrier_service = None

    @api.multi
    def get_phone_shipment_out(self):
        self.ensure_one()
        if self.partner_id.mobile:
            return self.partner_id.mobile
        if self.partner_id.phone:
            return self.partner_id.phone
        return self.company_id.phone if self.company_id.phone else ''

    @api.multi
    def get_carrier_employee(self):
        return self.env.user.employee_ids and self.env.user.employee_ids[0].id


    @api.multi
    def send_shipment_api(self):
        self.ensure_one()
        if not self.carrier_id:
            raise exceptions.Warning(_('No carrier'), _('Shipment "%s" not have carrier') % self.name)

        api = self.env['carrier.api'].search([('carriers', 'in', [self.carrier_id.id])],
            limit=1)
        if not api:
            raise exceptions.Warning(_('No api'), _('Carrier "%s" not have API') % self.carrier.name)

        if not self.partner_id.street or not self.partner_id.zip \
                or not self.partner_id.city or not self.partner_id.country_id:
            raise exceptions.Warning(
                _('Address error'),
                _('Shipment "%s" not have address details: street, zip, city or country.') % self.name)
        send_shipment = getattr(self, 'send_%s' % api.method)
        refs, labs = send_shipment(api)

        if labs:
            fname = _('%s label %s.pdf') % (api.method, datetime.now().strftime("%d/%m/%y %H:%M:%S"))
            self.env['ir.attachment'].create({
                'name': fname,
                'datas': base64.b64encode(open(labs[0], "rb").read()),
                'datas_fname': fname,
                'res_model':  'stock.picking',
                'res_id': self.id,
                'type': 'binary'
            })
        return refs, labs

    @api.multi
    def barcode_send_shipment(self):
        if self.carrier_delivery:
            model = 'carrier.print.shipment'
        else:
            model = 'carrier.send.shipment'
        wizard = self.env[model].create({})
        wizard.with_context(from_barcode=True,active_ids=[self.id]).default_get([])
        if self.carrier_delivery:
            wizard.with_context(from_barcode=True,active_ids=[self.id]).action_print()
        else:
            wizard.with_context(from_barcode=True,active_ids=[self.id]).action_send()
        return wizard.labels
