# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.prestashoperpconnect.unit.import_synchronizer import SaleOrderImporter


@prestashop(replacing=SaleOrderImporter)
class SaleOrderPackImporter(SaleOrderImporter):

    def _after_import(self, binding):
        binding.openerp_id.expand_packs()
        return super(SaleOrderPackImporter, self)._after_import(binding)
