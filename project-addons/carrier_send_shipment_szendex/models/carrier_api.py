# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, exceptions, _
import os
import urllib2
import socket
try:
    import genshi
    import genshi.template
except (ImportError, IOError) as err:
    import logging
    logging.getLogger(__name__).warn('Module genshi is not available')

loader = genshi.template.TemplateLoader(
    os.path.join(os.path.dirname(__file__), 'template'),
    auto_reload=True)


class CarrierApi(models.Model):
    _inherit = 'carrier.api'

    method = fields.Selection(selection_add=[('szendex', 'Szendex')])

    def szendex_url(self):
        """
        szendex URL connection

        :param debug: If set to true, use Envialia test URL
        """
        if self.debug:
            return 'http://81.46.230.160/WSNexus/ControladorWSCliente.asmx?WSDL'
        else:
            return 'http://81.46.230.160/WSNexus/ControladorWSCliente.asmx?WSDL'

    def connect_szendex(self, url, xml):
        """
            Connect to the Webservices and return XML data from szendex

            :param url: url service.
            :param xml: XML data.

            Return XML object
        """
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'Content-Type': 'text/xml; charset=utf-8',
            'Content-Length': len(xml),
        }
        request = urllib2.Request(url, xml, headers)
        try:
            response = urllib2.urlopen(request, timeout=100)
            return response.read()
        except socket.timeout:
            return
        except socket.error:
            return

    def validate_user_szendex(self, retry=False):
        vals = {
            'Nombre': self.username,
            'Password': self.password,
        }
        tmpl = loader.load('login.xml')
        xml = tmpl.generate(**vals).render()
        result = self.connect_szendex(self.szendex_url(), xml)
        if len(result.split('GUID')) == 3:
            guid_node = result.split('GUID')[1][4:-5]
            return guid_node
        else:
            if retry:
                raise Exception('Unkown error: %s' % result)
            self.disconnect_user_szendex()
            return self.validate_user_szendex(retry=True)

    def disconnect_user_szendex(self):
        vals = {
            'Nombre': self.username,
            'Password': self.password,
        }
        tmpl = loader.load('logout.xml')
        xml = tmpl.generate(**vals).render()
        self.connect_szendex(self.szendex_url(), xml)
        return True

    def send_picking_szendex(self, vals):
        tmpl = loader.load('send_picking.xml')
        xml = tmpl.generate(**vals).render()
        xml = xml.replace('&lt;', '<').replace('&gt;', '>')
        response = self.connect_szendex(self.szendex_url(), xml.encode('utf-8'))
        if len(response.split('REFERENCIAENTREGA')) == 3:
            return response.split('REFERENCIAENTREGA')[1][4:-5]
        else:
            raise Exception(response)

    def label_szendex(self, vals):
        tmpl = loader.load('print_label.xml')
        xml = tmpl.generate(**vals).render()
        response = self.connect_szendex(self.szendex_url(), xml)
        if len(response.split('ImprimirEtiquetaResult')) == 3:
            return response.split('ImprimirEtiquetaResult')[1][74:-27]
        else:
            raise Exception(response)

    def test_szendex(self):
        '''
        Test Envialia connection
        '''
        self.ensure_one()
        message = 'Connection unknown result'
        try:
            self.validate_user_szendex()
            message = 'Correct'
        except Exception:
            message = 'Fail'
        raise exceptions.Warning(_('Connection test'), message)
