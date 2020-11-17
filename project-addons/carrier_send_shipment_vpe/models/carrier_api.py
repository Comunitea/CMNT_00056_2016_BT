# -*- coding: utf-8 -*-
# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, exceptions, _
import os
import urllib2
import socket
from xml.dom.minidom import parseString
from datetime import datetime, timedelta

import logging

logger = logging.getLogger(__name__)

try:
    import genshi
    import genshi.template
except (ImportError, IOError):

    logger.warn("Module genshi is not available")

loader = genshi.template.TemplateLoader(
    os.path.join(os.path.dirname(__file__), "template"), auto_reload=True
)


class CarrierApi(models.Model):
    _inherit = "carrier.api"

    method = fields.Selection(selection_add=[("vpe", "vpe")])
    vpe_agencia = fields.Char()
    vpe_token_validity = fields.Datetime()
    vpe_token = fields.Char()

    def vpe_url(self):
        """
        vpe URL connection
        """
        if self.debug:
            raise Exception()
        else:
            urls = {
                "login": "http://ws.setotrans.com:7499/SOAP?service=LoginWSService",
                "grabar": "http://ws.setotrans.com:7499/SOAP?service=WebServService",
            }
        return urls

    def connect_vpe(self, url, xml):
        """
            Connect to the Webservices and return XML data from vpe

            :param url: url service.
            :param xml: XML data.

            Return XML object
        """
        headers = {
            "Content-Type": "application/soap+xml; charset=utf-8",
            "Content-Length": len(xml),
        }
        logger.debug("request {}".format(xml))
        request = urllib2.Request(url, xml, headers)
        try:
            response = urllib2.urlopen(request, timeout=100)
            response_data = response.read()
            logger.debug("response {}".format(response_data))
            return response_data
        except socket.timeout:
            return
        except socket.error:
            return

    def get_vpe_token(self):
        if self.vpe_token_validity and datetime.now() < fields.Datetime.from_string(
            self.vpe_token_validity
        ):
            return self.vpe_token
        url = self.vpe_url()["login"]
        vals = {
            "codigo_agencia": self.vpe_agencia,
            "codigo_usuario": self.username,
            "password": self.password,
        }
        tmpl = loader.load("login.xml")
        xml = tmpl.generate(**vals).render()
        result = self.connect_vpe(url, xml)
        result_xml = parseString(result)
        id_node = result_xml.getElementsByTagName("ID")
        if id_node:
            token = id_node[0].firstChild.data
            self.vpe_token = token
            self.vpe_token_validity = datetime.now() + timedelta(minutes=15)
            return token

    def send_picking_vpe(self, vals):
        tmpl = loader.load("send_picking.xml")
        vals["token"] = self.get_vpe_token()
        vals["codigo_agencia"] = self.vpe_agencia
        vals["codigo_usuario"] = self.username
        xml = tmpl.generate(**vals).render()
        response = self.connect_vpe(self.vpe_url()["grabar"], xml.encode("utf-8"))
        response_xml = parseString(response)
        picking_ref = response_xml.getElementsByTagName("v1:strAlbaranOut")
        if picking_ref:
            return picking_ref[0].firstChild.data
        else:
            raise Exception(response)

    def label_vpe(self, vals):
        tmpl = loader.load("print_label.xml")
        vals["token"] = self.get_vpe_token()
        vals["codigo_agencia"] = self.vpe_agencia
        xml = tmpl.generate(**vals).render()
        response = self.connect_vpe(self.vpe_url()["grabar"], xml)
        import pdb; pdb.set_trace()
        response_xml = parseString(response)
        tag_data = response_xml.getElementsByTagName("v1:strEtiqueta")
        if tag_data:
            tag_xml = parseString(tag_data[0].firstChild.data)
            return tag_xml.getElementsByTagName('ENVIO')[0].getAttribute('V_ETIQUETA')
        else:
            raise Exception(response)

    def test_vpe(self):
        """
        Test vpe connection
        """
        self.ensure_one()
        message = "Connection unknown result"
        try:
            self.get_vpe_token()
            message = "Correct"
        except Exception:
            message = "Fail"
        raise exceptions.Warning(_("Connection test"), message)
