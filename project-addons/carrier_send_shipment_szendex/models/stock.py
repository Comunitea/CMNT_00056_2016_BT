# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
from openerp.addons.carrier_send_shipment.tools import unaccent, unspaces
from datetime import datetime, date
from base64 import decodestring
import logging
import tempfile
logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    @api.multi
    def send_szendex(self, carrier_api):
        '''
        Send shipments out to szendex
        :param api: obj
        Return references, labels, errors
        '''

        references = []
        labels = []

        default_service = carrier_api.get_default_carrier_service()
        guid = carrier_api.validate_user_szendex()
        for picking in self:
            service = picking.carrier_service or picking.carrier_id.service or default_service
            if not service:
                raise exceptions.Warning(_('Api service error'), _('Select a service or default service in szendex API'))

            notes = ''
            if picking.carrier_notes:
                notes = '%s\n' % picking.carrier_notes

            packages = picking.number_of_packages
            if not packages:
                packages = 1
            company_partner = self.sale_store_id.partner_id or \
                self.picking_type_id.warehouse_id.partner_id or \
                self.company_id.partner_id

            data = {
                'GUID': guid,
                'remitente_nombre': company_partner.name,
                'RecogidaDireccion': company_partner.street,
                'RecogidaCodigoPostal': company_partner.zip,
                'RecogidaPais': company_partner.country_id.name,
                'RecogidaPoblacion': company_partner.city,
                'RecogidaTelefono': company_partner.phone,
                'RecogidaEmail': company_partner.email,
                'RecogidaObservacion': notes,
                'RecogidaCodigoTipoServicio': service.code,
                'RecogidaFecha': datetime.now().strftime('%Y-%m-%dT00:00:00'),
                'destinatario_nombre': picking.partner_id.name,
                'EntregaDireccion': picking.partner_id.street,
                'EntregaCodigoPostal': picking.partner_id.zip,
                'EntregaPais': picking.partner_id.country_id.name,
                'EntregaPoblacion': picking.partner_id.city,
                'EntregaTelefono': picking.partner_id.phone,
                'EntregaEmail': picking.partner_id.email,
                'EntregaMovil': picking.partner_id.mobile,
                'total_bultos': packages,
            }

            if carrier_api.weight:
                weight = picking.weight_edit
                data['peso_bulto'] = str(weight / packages).replace('.', ',')

            reference = carrier_api.send_picking_szendex(data)
            picking.write({
                'carrier_tracking_ref': reference,
                'carrier_service': service.id,
                'carrier_delivery': True,
                'carrier_send_date': datetime.now(),
                'carrier_send_employee': self.env.user.employee_ids and self.env.user.employee_ids[0].id or False,
                })
            logger.info('Send Picking %s' % (picking.name))
            references.append(picking.name)

            labels += picking.print_labels_szendex(carrier_api, guid)
        carrier_api.disconnect_user_szendex()
        return references, labels

    @api.multi
    def print_labels_szendex(self, carrier_api, guid=False):
        if not guid:
            guid = carrier_api.validate_user_szendex()

        labels = []
        dbname = self.env.cr.dbname

        for picking in self:
            if not picking.carrier_tracking_ref:
                logger.error(
                    'Picking %s has not been sent by szendex.'
                    % (picking.name))
                continue

            vals = {
                'reference': picking.carrier_tracking_ref,
                'guid': guid
            }

            reference = picking.carrier_tracking_ref

            label = carrier_api.label_szendex(vals)
            if not label:
                logger.error(
                    'Label for picking %s is not available from szendex.'
                    % picking.name)
                continue
            with tempfile.NamedTemporaryFile(
                    prefix='%s-szendex-%s-' % (dbname, reference),
                    suffix='.pdf', delete=False) as temp:
                temp.write(decodestring(label)) # szendex PDF file
            logger.info(
                'Generated tmp label %s' % (temp.name))
            temp.close()
            labels.append(temp.name)
        picking.write({'carrier_printed': True})

        return labels
