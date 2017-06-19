# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import tempfile
from correosexpress.picking import Picking
from datetime import datetime
from correosexpress.utils import services as correosexpress_services
from openerp import models, api, exceptions, _
from openerp.addons.carrier_send_shipment.tools import unaccent

logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def correosexpress_picking_data(self, api, service, price=None,
                                    weight=False):
        '''
        Correos express Picking Data
        :param api: obj
        :param shipment: obj
        :param service: str
        :param price: string
        :param weight: bol
        Return data
        '''
        self.ensure_one()
        packages = self.number_of_packages
        if not packages:
            packages = 1

        remitente_partner = self.picking_type_id.warehouse_id.partner_id or \
            self.company_id.partner_id

        if api.reference_origin and hasattr(self, 'origin'):
            code = self.origin
        else:
            code = self.name

        notes = ''
        if self.carrier_notes:
            notes = '%s\n' % self.carrier_notes
        data = {
            'solicitante': api.solicitante,
            'ref': code,
            'codRte': api.cod_rte,
            'nomRte': remitente_partner.name,
            'nifRte': remitente_partner.vat,
            'dirRte':
                unaccent(remitente_partner.street) + ' ' +
                unaccent(remitente_partner.street2 or ''),
            'pobRte': remitente_partner.city,
            'codPosNacRte': remitente_partner.zip,
            'paisISORte': remitente_partner.country_id.code,
            'codPosIntRte': remitente_partner.zip,
            'telefRte': remitente_partner.phone,
            'emailRte': remitente_partner.email,
            'nomDest': self.partner_id.name,
            'nifDest': self.partner_id.vat,
            'dirDest':
                unaccent(self.partner_id.street) + ' ' +
                unaccent(self.partner_id.street2 or ''),
            'pobDest': self.partner_id.city,
            'codPosNacDest': self.partner_id.zip,
            'paisISODest': self.partner_id.country_id.code,
            'codPosIntDest': self.partner_id.zip,

            'contacDest': self.partner_id.name,
            'telefDest': self.partner_id.phone,
            'emailDest': self.partner_id.email,
            'telefOtrs': self.partner_id.mobile,
            'observac': notes,
            'numBultos': str(packages),
            'kilos': str(self.weight_net_edit),
            'portes': 'P',
            'seguro': str(api.insurance),
            'entrSabado': 'N',
            'tipoEtiqueta': '1',
        }
        data['lista_bultos'] = [{'orden': x} for x in range(1, packages + 1)]
        correosexpress_service = correosexpress_services().get(service.code)
        if correosexpress_service:
            data['producto'] = correosexpress_service
        else:
            raise exceptions.Warning(
                _('Product error'),
                _('Service with code %s not found') % service.code)

        if self.cash_on_delivery and price:
            data['reembolso'] = str(price)
        return data

    @api.multi
    def send_correosexpress(self, api):
        '''
        Send shipments out to Correos express
        Return references, labels, errors
        '''
        references = []
        labels = []
        default_service = api.get_default_carrier_service()
        dbname = self.env.cr.dbname
        with Picking(api.username, api.password, api.debug) as picking_api:
            for picking in self:
                service = picking.carrier_service or \
                        picking.carrier_id.service or default_service
                if not service:
                    raise exceptions.Warning(
                        _('Api service error'),
                        _('Select a service or default service in º\
Correos express API'))

                price = None
                if picking.cash_on_delivery:
                    price = picking.amount_total
                    if not price:
                        raise exceptions.Warning(
                            _('Picking error'),
                            _('Shipment "%s" not have price and send \
cashondelivery') % picking.name)

                data = picking.correosexpress_picking_data(
                    api, service, price, api.weight)
                reference, returned_labels, error = picking_api.create(data)
                if error:
                    raise exceptions.Warning(_('API Error'), error)
                if reference:
                    picking.write({
                        'carrier_tracking_ref': reference,
                        'carrier_service': service.id,
                        'carrier_delivery': True,
                        'carrier_send_date': datetime.now(),
                        'carrier_send_employee':
                            self.env.user.employee_ids and
                            self.env.user.employee_ids[0].id or False,
                        })
                    logger.info(
                        'Send shipment %s' % (picking.name))
                    references.append(picking.name)
                else:
                    logger.error(
                        'Not send shipment %s.' % (picking.name))
                if returned_labels:
                    x = 0
                    for label in returned_labels:
                        with tempfile.NamedTemporaryFile(
                                prefix='%s-correosexpress-%s-%s' %
                                (dbname, reference, x),
                                suffix='.pdf', delete=False) as temp:
                            temp.write(label)
                        logger.info(
                            'Generated tmp label %s' % (temp.name))
                        temp.close()
                        labels.append(temp.name)
                        x += 1
                else:
                    raise exceptions.Warning(_('Label error'), _('No label'))
        return references, labels

    @api.multi
    def print_labels_correosexpress(self, api):
        '''
        Get labels from picking out from Correos express
        Not available labels from Correos express API. Not return labels
        '''
        raise NotImplementedError
