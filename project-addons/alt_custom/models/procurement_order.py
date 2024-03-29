# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import _, fields, models, SUPERUSER_ID
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    def make_po(self, cr, uid, ids, context=None):
        """Resolve the purchase from procurement, which may result in a new PO creation, a new PO line creation or a quantity change on existing PO line.
        Note that some operations (as the PO creation) are made as SUPERUSER because the current user may not have rights to do it (mto product launched by a sale for example)

        @return: dictionary giving for each procurement its related resolving PO line.
        """
        res = {}
        company = (
            self.pool.get("res.users").browse(cr, uid, uid, context=context).company_id
        )
        po_obj = self.pool.get("purchase.order")
        po_line_obj = self.pool.get("purchase.order.line")
        seq_obj = self.pool.get("ir.sequence")
        pass_ids = []
        linked_po_ids = []
        sum_po_line_ids = []
        for procurement in self.browse(cr, uid, ids, context=context):
            ctx_company = dict(context or {}, force_company=procurement.company_id.id)
            partner = self._get_product_supplier(
                cr, uid, procurement, context=ctx_company
            )
            if not partner:
                self.message_post(
                    cr,
                    uid,
                    [procurement.id],
                    _("There is no supplier associated to product %s")
                    % (procurement.product_id.name),
                )
                res[procurement.id] = False
            else:
                schedule_date = self._get_purchase_schedule_date(
                    cr, uid, procurement, company, context=context
                )
                purchase_date = self._get_purchase_order_date(
                    cr, uid, procurement, company, schedule_date, context=context
                )
                line_vals = self._get_po_line_values_from_proc(
                    cr,
                    uid,
                    procurement,
                    partner,
                    company,
                    schedule_date,
                    context=ctx_company,
                )
                # look for any other draft PO for the same supplier, to attach the new line on instead of creating a new draft one
                if procurement.rule_id.group_propagation_option == "propagate":
                    available_draft_po_ids = po_obj.search(
                        cr,
                        uid,
                        [
                            ("partner_id", "=", partner.id),
                            ("state", "=", "draft"),
                            (
                                "picking_type_id",
                                "=",
                                procurement.rule_id.picking_type_id.id,
                            ),
                            ("location_id", "=", procurement.location_id.id),
                            ("company_id", "=", procurement.company_id.id),
                            ("dest_address_id", "=", procurement.partner_dest_id.id),
                            ("procurement_group_id", "=", procurement.group_id.id),
                        ],
                        context=context,
                    )
                else:
                    available_draft_po_ids = po_obj.search(
                        cr,
                        uid,
                        [
                            ("partner_id", "=", partner.id),
                            ("state", "=", "draft"),
                            (
                                "picking_type_id",
                                "=",
                                procurement.rule_id.picking_type_id.id,
                            ),
                            ("location_id", "=", procurement.location_id.id),
                            ("company_id", "=", procurement.company_id.id),
                            ("dest_address_id", "=", procurement.partner_dest_id.id),
                            ("procurement_group_id", "=", False),
                        ],
                        context=context,
                    )
                if available_draft_po_ids:
                    po_id = available_draft_po_ids[0]
                    po_rec = po_obj.browse(cr, uid, po_id, context=context)

                    po_to_update = {
                        "origin": ", ".join(
                            filter(None, set([po_rec.origin, procurement.origin]))
                        )
                    }
                    # if the product has to be ordered earlier those in the existing PO, we replace the purchase date on the order to avoid ordering it too late
                    if (
                        datetime.strptime(
                            po_rec.date_order, DEFAULT_SERVER_DATETIME_FORMAT
                        )
                        > purchase_date
                    ):
                        po_to_update.update(
                            {
                                "date_order": purchase_date.strftime(
                                    DEFAULT_SERVER_DATETIME_FORMAT
                                )
                            }
                        )
                    po_obj.write(cr, uid, [po_id], po_to_update, context=context)
                    # look for any other PO line in the selected PO with same product and UoM to sum quantities instead of creating a new po line
                    available_po_line_ids = po_line_obj.search(
                        cr,
                        uid,
                        [
                            ("order_id", "=", po_id),
                            ("product_id", "=", line_vals["product_id"]),
                            ("product_uom", "=", line_vals["product_uom"]),
                        ],
                        context=context,
                    )
                    if available_po_line_ids:
                        po_line = po_line_obj.browse(
                            cr, uid, available_po_line_ids[0], context=context
                        )
                        po_line_id = po_line.id
                        new_qty, new_price = self._calc_new_qty_price(
                            cr, uid, procurement, po_line=po_line, context=context
                        )

                        if new_qty > po_line.product_qty:
                            po_line_obj.write(
                                cr,
                                SUPERUSER_ID,
                                po_line.id,
                                {"product_qty": new_qty, "price_unit": new_price},
                                context=context,
                            )
                            self.update_origin_po(
                                cr, uid, po_rec, procurement, context=context
                            )
                            sum_po_line_ids.append(procurement.id)
                    else:
                        line_vals.update(order_id=po_id)
                        po_line_id = po_line_obj.create(
                            cr, SUPERUSER_ID, line_vals, context=context
                        )
                        linked_po_ids.append(procurement.id)
                else:
                    name = (
                        seq_obj.get(cr, uid, "purchase.order", context=ctx_company)
                        or _("PO: %s") % procurement.name
                    )
                    po_vals = {
                        "name": name,
                        "origin": procurement.origin,
                        "partner_id": partner.id,
                        "location_id": procurement.location_id.id,
                        "picking_type_id": procurement.rule_id.picking_type_id.id,
                        "pricelist_id": partner.property_product_pricelist_purchase.id,
                        "currency_id": partner.property_product_pricelist_purchase
                        and partner.property_product_pricelist_purchase.currency_id.id
                        or procurement.company_id.currency_id.id,
                        "date_order": purchase_date.strftime(
                            DEFAULT_SERVER_DATETIME_FORMAT
                        ),
                        "company_id": procurement.company_id.id,
                        "fiscal_position": po_obj.onchange_partner_id(
                            cr,
                            uid,
                            None,
                            partner.id,
                            context=dict(context, company_id=procurement.company_id.id),
                        )["value"]["fiscal_position"],
                        "payment_term_id": partner.property_supplier_payment_term.id
                        or False,
                        "dest_address_id": procurement.partner_dest_id.id,
                    }
                    if procurement.rule_id.group_propagation_option == "propagate":
                        po_vals["procurement_group_id"] = procurement.group_id.id
                    po_id = self.create_procurement_purchase_order(
                        cr,
                        SUPERUSER_ID,
                        procurement,
                        po_vals,
                        line_vals,
                        context=dict(context, company_id=po_vals["company_id"]),
                    )
                    po_line_id = (
                        po_obj.browse(cr, uid, po_id, context=context).order_line[0].id
                    )
                    pass_ids.append(procurement.id)
                res[procurement.id] = po_line_id
                self.write(
                    cr,
                    uid,
                    [procurement.id],
                    {"purchase_line_id": po_line_id},
                    context=context,
                )
        if pass_ids:
            self.message_post(
                cr,
                uid,
                pass_ids,
                body=_("Draft Purchase Order created"),
                context=context,
            )
        if linked_po_ids:
            self.message_post(
                cr,
                uid,
                linked_po_ids,
                body=_(
                    "Purchase line created and linked to an existing Purchase Order"
                ),
                context=context,
            )
        if sum_po_line_ids:
            self.message_post(
                cr,
                uid,
                sum_po_line_ids,
                body=_("Quantity added in existing Purchase Order Line"),
                context=context,
            )
        return res
