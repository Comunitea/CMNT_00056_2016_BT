# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, exceptions, _


class CarrierGetLabel(Wizard):

    codes = fields.Char('Codes', required=True,
        help='Introduce codes or tracking reference of shipments separated by commas.')

    attachments = fields.One2Many('ir.attachment', None, 'Attachments',
        states={
            'invisible': Not(Bool(Eval('attachments'))),
            'readonly': True,
            })

    'Carrier Get Label'
    __name__ = "carrier.get.label"
    start = StateView('carrier.get.label.start',
        'carrier_send_shipments.carrier_get_label_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Get', 'get', 'tryton-ok', default=True),
            ])
    get = StateTransition()
    result = StateView('carrier.get.label.result',
        'carrier_send_shipments.carrier_get_label_result_view_form', [
            Button('Close', 'end', 'tryton-close'),
            ])

    def transition_get(self):
        pool = Pool()
        Attachment = pool.get('ir.attachment')
        Shipment = pool.get('stock.shipment.out')
        API = pool.get('carrier.api')

        codes = [l.strip() for l in self.start.codes.split(',')]
        shipments = Shipment.search([
                ('state', 'in', _SHIPMENT_STATES),
                ['OR',
                    ('code', 'in', codes),
                    ('carrier_tracking_ref', 'in', codes),
                ]])

        if not shipments:
            return 'result'

        apis = {}
        for shipment in shipments:
            if not shipment.carrier:
                continue
            carrier_apis = API.search([('carriers', 'in', [shipment.carrier.id])],
                limit=1)
            if not carrier_apis:
                continue
            api, = carrier_apis

            if apis.get(api.method):
                shipments = apis.get(api.method)
                shipments.append(shipment)
            else:
                shipments = [shipment]
            apis[api.method] = shipments

        attachments = []
        for method, shipments in apis.iteritems():
            api, = API.search([('method', '=', method)],
                limit=1)
            print_label = getattr(Shipment, 'print_labels_%s' % method)
            labels = print_label(api, shipments)

            for label, shipment in zip(labels, shipments):
                attach = {
                    'name': datetime.now().strftime("%y/%m/%d %H:%M:%S"),
                    'type': 'data',
                    'data': fields.Binary.cast(open(label, "rb").read()),
                    'description': '%s - %s' % (shipment.code, method),
                    'resource': '%s' % str(shipment),
                    }

                attachments.append(attach)

        attachments = Attachment.create(attachments)
        self.result.attachments = attachments

        return 'result'

    def default_result(self, fields):
        return {
            'attachments': [a.id
                for a in getattr(self.result, 'attachments', [])],
            }
