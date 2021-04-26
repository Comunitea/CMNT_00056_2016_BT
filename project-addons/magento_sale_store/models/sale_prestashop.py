# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.prestashoperpconnect.unit.mapper import SaleOrderMapper
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.connector.unit.mapper import mapping


@prestashop(replacing=SaleOrderMapper)
class SaleOrderMapperAddStore(SaleOrderMapper):

    @mapping
    def store_id(self, record):
        binder = self.binder_for("prestashop.shop")
        shop_store = binder.to_openerp(record["id_shop"])
        sale_store = self.env["prestashop.shop"].browse(shop_store).store_id
        return {"sale_store_id": sale_store.id}
