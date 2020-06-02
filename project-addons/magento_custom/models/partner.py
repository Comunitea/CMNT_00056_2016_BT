# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api
from openerp.addons.magentoerpconnect.partner import (
    BaseAddressImportMapper,
    CompanyImportMapper,
)
from openerp.addons.magentoerpconnect.backend import magento
from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.magento_sale_store.models.magento_store import (
    PartnerImportMapperStoreACcount,
)


@magento(replacing=CompanyImportMapper)
class CustomCompanyImportMapper(CompanyImportMapper):
    direct = BaseAddressImportMapper.direct


@magento(replacing=PartnerImportMapperStoreACcount)
class PartnerImportMapperMedical(PartnerImportMapperStoreACcount):
    # direct = PartnerImportMapperStoreACcount.direct + [('codigo_prescriptor', 'medical_code')]

    @mapping
    def medical_code(self, record):
        [{u"attribute_code": u"codigo_prescriptor", u"value": u"ACQ-5012"}]
        if record.get("custom_attributes"):
            for attribute in record.get("custom_attributes"):
                if attribute.get("attribute_code") == "codigo_prescriptor":
                    return {"medical_code": attribute.get("value")}


class MagentoResPartner(models.Model):

    _inherit = "magento.res.partner"

    @api.model
    def create(self, vals):
        res = super(MagentoResPartner, self).create(vals)
        if res.openerp_id and res.taxvat:
            res.openerp_id.vat = res.taxvat.upper()
        return res

    @api.multi
    def write(self, vals):
        if vals.get("taxvat"):
            for res in self:
                res.openerp_id.vat = vals.get("taxvat").upper()
        return super(MagentoResPartner, self).write(vals)
