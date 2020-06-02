# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.magentoerpconnect.backend import magento
from openerp.addons.magentoerpconnect.backend import magento2000
from openerp.addons.magentoerpconnect.sale import (
    SaleOrderImporter,
    SaleOrderImporter2000,
)


@magento(replacing=SaleOrderImporter)
class SaleOrderPackImporter(SaleOrderImporter):
    def _after_import(self, binding):
        binding.openerp_id.expand_packs()
        return super(SaleOrderPackImporter, self)._after_import(binding)


@magento2000(replacing=SaleOrderImporter2000)
class SaleOrderPackImporter2000(SaleOrderImporter2000):
    def _after_import(self, binding):
        binding.openerp_id.expand_packs()
        return super(SaleOrderPackImporter2000, self)._after_import(binding)
