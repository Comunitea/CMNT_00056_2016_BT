# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.magentoerpconnect.sale import SaleOrderImportMapper
from openerp.addons.magentoerpconnect.backend import magento
from openerp.addons.connector.unit.mapper import mapping


@magento(replacing=SaleOrderImportMapper)
class SaleOrderStoreImportMapper(SaleOrderImportMapper):
    @mapping
    def store_id(self, record):
        binder = self.binder_for("magento.store")
        magento_store = binder.to_openerp(record["store_id"])
        sale_store = self.env["magento.store"].browse(magento_store).store_id
        return {"sale_store_id": sale_store.id}

    @mapping
    def user_id(self, record):
        binder = self.binder_for("magento.res.partner")
        partner_id = binder.to_openerp(record["customer_id"], unwrap=True)
        assert partner_id is not None, (
            "customer_id %s should have been imported in "
            "SaleOrderImporter._import_dependencies" % record["customer_id"]
        )
        partner = self.env["res.partner"].browse(partner_id)
        if partner.user_id:
            return {"user_id": partner.user_id.id}
        elif self.backend_record.default_user_id:
            return {"user_id": self.backend_record.default_user_id.id}
        else:
            return super(SaleOrderStoreImportMapper, self).user_id(record)
