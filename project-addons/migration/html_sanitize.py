#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from odoolib import OdooConnect
import re


def replaceHtml(text):
    text = (
        text.replace("&nbsp;", " ")
        .replace("&iacute;", u"í")
        .replace("&iacute;", u"í")
        .replace("&oacute;", u"ó")
        .replace("&eacute;", u"é")
        .replace("&aacute;", u"á")
        .replace("&uacute;", u"ú")
        .replace("&Oacute;", u"Ó")
        .replace("&Aacute;", u"Á")
        .replace("&Iacute;", u"Í")
        .replace("&Eacute;", u"É")
        .replace("&Uacute;", u"Ú")
        .replace("&euro;", u"€")
        .replace("&ntilde;", u"ñ")
        .replace("&Ntilde;", u"Ñ")
        .replace("&deg;", u"º")
        .replace("&iexcl;", u"¡")
        .replace("&ndash;", u"–")
        .replace("&bull;", u"–")
        .replace("&hellip;", u"...")
        .replace("&rdquo;", u'"')
        .replace("&ldquo;", u'"')
        .replace("&lt;", u"<")
        .replace("&gt;", u">")
        .replace("&ordf;", u"ª")
        .replace("&ordm;", u"º")
        .replace("&amp;", u"&")
    )

    if "&" in text:
        print "TEXT: ", text
    return text


class HtmlSanitize(object):
    def __init__(self):
        try:
            self.odoo = OdooConnect()
            self.fix_product_texts()
            print ("Successfull migration")
        except Exception, e:
            print ("ERROR: ", (e))
            sys.exit(1)

    def fix_product_texts(self):
        product_ids = self.odoo.search(
            "product.product", ["|", ("active", "=", True), ("active", "=", False)]
        )
        x = re.compile(r"<[^<]*?/?>")
        for product_id in product_ids:
            product_data = self.odoo.read(
                "product.product", product_id, ["description_sale", "description"]
            )
            vals = {}
            if product_data["description_sale"]:
                vals["description_sale"] = replaceHtml(
                    x.sub("", product_data["description_sale"])
                )
            if product_data["description"]:
                vals["description"] = replaceHtml(
                    x.sub("", product_data["description"])
                )

            if vals:
                self.odoo.write("product.product", [product_id], vals)
        return True


HtmlSanitize()
