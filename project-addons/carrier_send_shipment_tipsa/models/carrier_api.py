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

    method = fields.Selection(selection_add=[("tipsa", "tipsa")])
    tipsa_agencia = fields.Char()
    tipsa_token_validity = fields.Datetime()
    tipsa_token = fields.Char()

    def tipsa_url(self):
        """
        tipsa URL connection
        """
        if self.debug:
            urls = {
                "login": "http://79.171.110.38:8097/SOAP?service=LoginWSService",
                "grabar": "http://79.171.110.38:8097/SOAP?service=WebServService",
            }
        else:
            urls = {
                "login": "http://webservices.tipsa-dinapaq.com/SOAP?service=LoginWSService",
                "grabar": "http://webservices.tipsa-dinapaq.com/SOAP?service=WebServService",
            }
        return urls

    def connect_tipsa(self, url, xml):
        """
            Connect to the Webservices and return XML data from tipsa

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

    def get_tipsa_token(self):
        if self.tipsa_token_validity and datetime.now() < fields.Datetime.from_string(
            self.tipsa_token_validity
        ):
            return self.tipsa_token
        url = self.tipsa_url()["login"]
        vals = {
            "codigo_agencia": self.tipsa_agencia,
            "codigo_usuario": self.username,
            "password": self.password,
        }
        tmpl = loader.load("login.xml")
        xml = tmpl.generate(**vals).render()
        result = self.connect_tipsa(url, xml)
        result_xml = parseString(result)
        id_node = result_xml.getElementsByTagName("ID")
        if id_node:
            token = id_node[0].firstChild.data
            self.tipsa_token = token
            self.tipsa_token_validity = datetime.now() + timedelta(minutes=15)
            return token

    def send_picking_tipsa(self, vals):
        tmpl = loader.load("send_picking.xml")
        vals["token"] = self.get_tipsa_token()
        vals["codigo_agencia"] = self.tipsa_agencia
        vals["codigo_usuario"] = self.username
        xml = tmpl.generate(**vals).render()
        response = self.connect_tipsa(self.tipsa_url()["grabar"], xml.encode("utf-8"))
        response_xml = parseString(response)
        picking_ref = response_xml.getElementsByTagName("v1:strAlbaranOut")
        if picking_ref:
            return picking_ref[0].firstChild.data
        else:
            raise Exception(response)

    def label_tipsa(self, vals):
        tmpl = loader.load("print_label.xml")
        vals["token"] = self.get_tipsa_token()
        vals["codigo_agencia"] = self.tipsa_agencia
        xml = tmpl.generate(**vals).render()
        response = self.connect_tipsa(self.tipsa_url()["grabar"], xml)
        response_xml = parseString(response)
        tag_data = response_xml.getElementsByTagName("v1:strEtiqueta")
        if tag_data:
            return tag_data[0].firstChild.data
        else:
            raise Exception(response)

    def test_tipsa(self):
        """
        Test Tipsa connection
        """
        self.ensure_one()
        message = "Connection unknown result"
        try:
            self.get_tipsa_token()
            message = "Correct"
        except Exception:
            message = "Fail"
        raise exceptions.Warning(_("Connection test"), message)
