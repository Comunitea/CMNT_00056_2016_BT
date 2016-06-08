# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
from datetime import datetime, date

class StockPicking(models.Model):
    _inherit = 'stock.picking'


    @api.multi
    def send_envialia(self, carrier_api):
        '''
        Send shipments out to envialia
        :param api: obj
        Return references, labels, errors
        '''

        references = []
        labels = []

        agency = carrier_api.envialia_agency
        customer = carrier_api.username
        password = carrier_api.password
        debug = carrier_api.debug

        default_service = carrier_api.get_default_carrier_service()

        with Picking(agency, customer, password, debug) as picking_api:
            for picking in self:
                service = picking.carrier_service or picking.carrier.service or default_service
                if not service:
                    raise exceptions.Warning(_('Api service error'), _('Select a service or default service in Envialia API'))

                if carrier_api.reference_origin and hasattr(shipment, 'origin'):
                    code = picking.origin  or picking.name
                else:
                    code = picking.name

                notes = ''
                if picking.carrier_notes:
                    notes = '%s\n' % shipment.carrier_notes

                packages = shipment.number_of_packages
                if not packages:
                    packages = 1

                data = {}
                data['agency_cargo'] = agency
                data['agency_origin'] = customer
                if not carrier_api.reference:
                    data['reference'] = code
                data['picking_date'] = date.today()
                data['service_code'] = str(service.code)
                data['company_name'] = unaccent(carrier_api.company.rec_name)
                data['company_code'] = customer
                data['company_phone'] = carrier_api.phone
                data['customer_name'] = unaccent(picking.partner_id.name)
                data['customer_contact_name'] = unaccent(picking.partner_id.name)
                data['customer_street'] = unaccent(picking.partner_id.street)
                data['customer_city'] = unaccent(picking.partner_id.city)
                data['customer_zip'] = picking.partner_id.zip
                data['customer_phone'] = unspaces(picking.partner_id.phone)
                data['document'] = packages
                if picking.carrier_cashondelivery:
                    price_ondelivery = picking.amount_total
                    if not price_ondelivery:
                        raise exceptions.Warning(_('Picking error'), _('Picking "%s" not have price and send cashondelivery') % picking.name)
                        continue
                    data['cash_ondelivery'] = str(price_ondelivery)
                data['ref'] = code
                data['notes'] = unaccent(notes)
                if carrier_api.weight and hasattr(shipment, 'weight_func'):
                    weight = shipment.weight_func
                    if weight == 0:
                        weight = 1
                    if carrier_api.weight_api_unit:
                        if shipment.weight_uom:
                            weight = Uom.compute_qty(
                                shipment.weight_uom, weight, carrier_api.weight_api_unit)
                        elif carrier_api.weight_unit:
                            weight = Uom.compute_qty(
                                carrier_api.weight_unit, weight, carrier_api.weight_api_unit)
                    data['weight'] = str(weight)

                # Send shipment data to carrier
                envialia = picking_api.create(data)

                if not envialia:
                    logger.error('Not send picking %s.' % (picking.name))
                if envialia and envialia.get('reference'):
                    reference = envialia.get('reference')
                    picking.write({
                        'carrier_tracking_ref': reference,
                        'carrier_service': service,
                        'carrier_delivery': True,
                        'carrier_send_date': datetime.now,
                        'carrier_send_employee': self.env.user.employee_ids and self.env.user.employee_ids[0] or False,
                        })
                    logger.info('Send Picking %s' % (picking.name))
                    references.append(picking.name)
                if envialia and envialia.get('error'):
                    error = envialia.get('error')
                    raise exceptions.Warning(_('Api error'), _('Not send shipment %s. %s') % (picking.name, error))

                labels += picking.print_labels_envialia(carrier_api)

        return references, labels

    @api.multi
    def print_labels_envialia(self, carrier_api):
        agency = carrier_api.envialia_agency
        username = carrier_api.username
        password = carrier_api.password
        debug = carrier_api.debug

        labels = []
        dbname = self.env.cr.dbname

        with Picking(agency, username, password, debug) as picking_api:
            for picking in self:
                if not picking.carrier_tracking_ref:
                    logger.error(
                        'Picking %s has not been sent by Envialia.'
                        % (picking.name))
                    continue

                data = {}
                data['agency_origin'] = data['agency_cargo'] = agency
                reference = picking.carrier_tracking_ref

                label = picking_api.label(reference, data)
                if not label:
                    logger.error(
                        'Label for picking %s is not available from Envialia.'
                        % picking.name)
                    continue
                with tempfile.NamedTemporaryFile(
                        prefix='%s-envialia-%s-' % (dbname, reference),
                        suffix='.pdf', delete=False) as temp:
                    temp.write(decodestring(label)) # Envialia PDF file
                logger.info(
                    'Generated tmp label %s' % (temp.name))
                temp.close()
                labels.append(temp.name)
            picking.write({'carrier_printed': True})

        return labels
