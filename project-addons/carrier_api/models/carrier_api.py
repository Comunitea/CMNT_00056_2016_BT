# -*- coding: utf-8 -*-
# © 2013 Zikzakmedia SL.
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _, exceptions


class CarrierApiService(models.Model):
    _name = 'carrier.api.service'

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code', required=True)
    default = fields.Boolean()
    carrier_api = fields.Many2one('carrier.api', 'API')


class CarrierApi(models.Model):
    _name = 'carrier.api'
    _rec_name = 'method'

    company = fields.Many2one('res.company', required=True,
                              default=lambda self: self.env.user.company_id.id)
    carriers = fields.Many2many('delivery.carrier', required=True)
    method = fields.Selection([], required=True)
    services = fields.One2many('carrier.api.service', 'carrier_api')

    vat = fields.Char(required=True)
    username = fields.Char(required=True)
    password = fields.Char(required=True)
    reference = fields.Boolean(help='Use reference from carrier', default=True)
    reference_origin = fields.Boolean(
        help='Use origin field as the reference record')
    weight = fields.Boolean(help='Send shipments with weight', default=True)
    weight_unit = fields.Many2one('product.uom', help='Default shipments unit')

    weight_api_unit = fields.Many2one('product.uom', help='Default API unit')
    phone = fields.Char()
    zips = fields.Text(
        'Zip', help='Zip codes not send to carrier, separated by comma')
    debug = fields.Boolean('Debug')

    @api.multi
    def get_default_carrier_service(self):
        """Get default service API"""
        self.ensure_one()
        for service in self.services:
            if service.default:
                return service
        raise exceptions.Warning(_('Service error'), _("API doesn't have default service"))

    @api.multi
    def test_connection(self):
        """
        Test connection Carrier API - Webservices
        Call method test_methodname
        """
        for carrier_api in self:
            test = getattr(self, 'test_%s' % self.method)
            test()
