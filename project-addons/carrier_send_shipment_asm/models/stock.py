# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import tempfile
from base64 import decodestring
from asm.picking import Picking
from datetime import datetime, date
from asm.utils import services as asm_services
from openerp import models, fields, api, exceptions, _
from openerp.addons.carrier_send_shipment.tools import unaccent

logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def asm_picking_data(self, api, service, price=None, weight=False):
        '''
        ASM Picking Data
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

        remitente_partner = self.sale_store_id.partner_id or \
            self.picking_type_id.warehouse_id.partner_id or \
            self.company_id.partner_id

        if api.reference_origin and hasattr(self, 'origin'):
            code = self.origin
        else:
            code = self.name

        notes = ''
        if self.carrier_notes:
            notes = '%s\n' % self.carrier_notes

        data = {}
        data['today'] = date.today()
        #~ data['portes'] =
        data['bultos'] = packages
        #~ data['volumen'] =
        #~ data['declarado'] =
        #~ data['dninob'] =
        #~ data['fechaentrega'] =
        data['retorno'] = '1' if self.asm_return else '0'
        #~ data['pod'] =
        #~ data['podobligatorio'] =
        #~ data['remite_plaza'] =
        data['remite_nombre'] = remitente_partner.name
        data['remite_direccion'] = unaccent(remitente_partner.street)
        data['remite_poblacion'] = unaccent(remitente_partner.city)
        data['remite_provincia'] = remitente_partner.state_id and unaccent(remitente_partner.state_id.name) or ''
        data['remite_pais'] = remitente_partner.country_id and remitente_partner.country_id.code
        data['remite_cp'] = remitente_partner.zip
        data['remite_telefono'] = remitente_partner.phone or ''
        #~ data['remite_movil'] =
        data['remite_email'] = remitente_partner.email or ''
        #~ data['remite_departamento'] =
        data['remite_nif'] = remitente_partner.vat
        #~ data['remite_observaciones'] =
        #~ data['destinatario_codigo'] =
        #~ data['destinatario_plaza'] =
        data['destinatario_nombre'] = unaccent(self.partner_id.name)
        data['destinatario_direccion'] = unaccent(self.partner_id.street)
        data['destinatario_poblacion'] = unaccent(self.partner_id.city)
        data['destinatario_provincia'] = self.partner_id.state_id and unaccent(self.partner_id.state_id.name) or ''
        data['destinatario_pais'] = self.partner_id.country_id and self.partner_id.country_id.code or ''
        data['destinatario_cp'] = self.partner_id.zip
        data['destinatario_telefono'] = self.partner_id.phone or ''
        data['destinatario_movil'] = self.partner_id.mobile or ''
        data['destinatario_email'] = self.partner_id.email or ''
        data['destinatario_observaciones'] = unaccent(notes)
        data['destinatario_att'] = unaccent(remitente_partner.name if remitente_partner.name else self.partner_id.name)
        #~ data['destinatario_departamento'] =
        #~ data['destinatario_nif'] =
        data['referencia_c'] = code
        #~ data['referencia_0'] = '12345'
        #~ data['importes_debido'] =
        #~ data['seguro'] =
        #~ data['seguro_descripcion'] =
        #~ data['seguro_importe'] =
        #~ data['etiqueta'] =
        #~ data['etiqueta_devolucion'] =
        #~ data['cliente_codigo'] =
        #~ data['cliente_plaza'] =
        #~ data['cliente_agente'] =

        asm_service = asm_services().get(service.code)
        if asm_service:
            data['servicio'] = asm_service['servicio']
            data['horario'] = asm_service['horario']

        if self.cash_on_delivery and price:
            data['importes_reembolso'] = price

        if weight and hasattr(self, 'weight_func'): # TODO: revisar campos pesos
            weight = self.weight_func
            if weight == 0:
                weight = 1
            if api.weight_api_unit:
                if self.weight_uom:
                    weight = Uom.compute_qty(
                        self.weight_uom, weight, api.weight_api_unit)
                elif api.weight_unit:
                    weight = Uom.compute_qty(
                        api.weight_unit, weight, api.weight_api_unit)
            data['peso'] = str(weight)

        return data

    @api.multi
    def send_asm(self, api):
        '''
        Send shipments out to asm
        Return references, labels, errors
        '''
        references = []
        labels = []

        default_service = api.get_default_carrier_service()
        dbname = self.env.cr.dbname

        with Picking(api.username, api.debug) as picking_api:
            for picking in self:
                service = picking.carrier_service or picking.carrier_id.service or default_service
                if not service:
                    raise exceptions.Warning(_('Api service error'), _('Select a service or default service in ASM API'))

                if not picking.partner_id.country_id:
                    raise exceptions.Warning(_('Partner error'), _('Add country in shipment "%s" partner') % picking.partner_id.name)

                price = None
                if picking.cash_on_delivery:
                    price = picking.amount_total
                    if not price:
                        raise exceptions.Warning(_('Picking error'), _('Shipment "%s" not have price and send cashondelivery') % picking.name)

                data = picking.asm_picking_data(api, service, price, api.weight)
                reference, label, error = picking_api.create(data)
                if reference:
                    picking.write({
                        'carrier_tracking_ref': reference,
                        'carrier_service': service.id,
                        'carrier_delivery': True,
                        'carrier_send_date': datetime.now(),
                        'carrier_send_employee': self.env.user.employee_ids and self.env.user.employee_ids[0].id or False,
                        })
                    logger.info(
                        'Send shipment %s' % (picking.name))
                    references.append(picking.name)
                else:
                    logger.error(
                        'Not send shipment %s.' % (picking.name))
                if label:
                    with tempfile.NamedTemporaryFile(
                            prefix='%s-asm-%s-' % (dbname, reference),
                            suffix='.pdf', delete=False) as temp:
                        temp.write(decodestring(label))
                    logger.info(
                        'Generated tmp label %s' % (temp.name))
                    temp.close()
                    labels.append(temp.name)
                else:
                    raise exceptions.Warning(_('Label error'), _('No label'))

                if error:
                    raise exceptions.Warning(_('API Error'), Error)
        return references, labels

    @api.multi
    def print_labels_asm(self, api):
        '''
        Get labels from picking out from ASM
        Not available labels from ASM API. Not return labels
        '''
        labels = []
        dbname = self.env.cr.dbname

        with Picking(api.username, api.debug) as picking_api:
            for picking in self:
                if not picking.carrier_tracking_ref:
                    logger.error(
                        'Picking %s has not been sent by ASM.'
                        % (picking.name))
                    continue

                reference = picking.carrier_tracking_ref

                data = {}
                data['codigo'] = reference
                label = picking_api.label(data)

                if not label:
                    logger.error(
                        'Label for picking %s is not available from ASM.'
                        % picking.name)
                    continue
                with tempfile.NamedTemporaryFile(
                        prefix='%s-asm-%s-' % (dbname, reference),
                        suffix='.pdf', delete=False) as temp:
                    temp.write(decodestring(label))
                logger.info(
                    'Generated tmp label %s' % (temp.name))
                temp.close()
                labels.append(temp.name)
            picking.write({'carrier_printed': True})
        return labels
