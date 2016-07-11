# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.magentoerpconnect.partner import BaseAddressImportMapper, CompanyImportMapper
from openerp.addons.magentoerpconnect.backend import magento
from openerp.addons.connector.unit.mapper import mapping

@magento(replacing=CompanyImportMapper)
class CustomCompanyImportMapper(CompanyImportMapper):
    direct = BaseAddressImportMapper.direct
