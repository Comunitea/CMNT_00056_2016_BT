# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _


class SaleStore(models.Model):

    _name = 'sale.store'

    name = fields.Char(required=True)
    journal_id = fields.Many2one('account.journal', 'Journal')
    active = fields.Boolean("Active", default=True)
    partner_id_in = fields.Many2one('res.partner', 'partner')
    logo_in = fields.Binary(string='logo')
    email_in = fields.Char(string='email')
    phone_in = fields.Char(string='phone')
    logo = fields.Binary(compute='_compute_partner_fields', readonly=True)
    email = fields.Char(compute='_compute_partner_fields', readonly=True)
    phone = fields.Char(compute='_compute_partner_fields', readonly=True)
    partner_id = fields.Many2one('res.partner', compute='_compute_partner_fields', readonly=True)
    default_account_id = fields.\
        Many2one('account.account',
                 'Default account for ecommerce customers importations')
    not_create_invoice_moves = fields.Boolean()

    @api.multi
    def _compute_partner_fields(self):
        for store in self:
            partner = store.partner_id_in
            if partner:
                store.logo = partner.image
                store.email = partner.email
                store.phone = partner.phone
                store.partner_id = partner
            else:
                store.logo = store.logo_in
                store.email = store.email_in
                store.phone = store.phone_in
                store.partner_id = self.env.user.company_id.partner_id

    @api.multi
    def action_view_config(self):
        return {
            'domain': "[('store','='," + str(self.id) + ")]",
            'name': _('Store configuration'),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'sale.store.config',
            'type': 'ir.actions.act_window',
            'context': "{'default_store': " + str(self.id) + "}"
        }


class SaleStoreConfig(models.Model):

    _name = 'sale.store.config'

    partner = fields.Many2one('res.partner', required=True)
    store = fields.Many2one('sale.store', required=True)
    zip = fields.Char(related='partner.zip', readonly=True)
    state_id = fields.Many2one('res.country.state', related='partner.state_id', readonly=True)
    value = fields.Reference(
        [('product.pricelist', 'Pricelist'),
         ('payment.mode', 'Payment mode'),
         ('account.payment.term', 'Payment term')])


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    sale_store_id = fields.Many2one('sale.store', 'Store', readonly=True,
                                    states={'draft': [('readonly', False)]})

    @api.model
    def _prepare_invoice(self, order, lines):
        res = super(SaleOrder, self)._prepare_invoice(order, lines)
        if order.sale_store_id:
            journal = order.sale_store_id.journal_id
            res['journal_id'] = journal.id
            res['sale_store_id'] = order.sale_store_id.id
        return res

    @api.multi
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        for obj in self:
            for picking in obj.picking_ids:
                picking.sale_store_id = obj.sale_store_id
        return res

    @api.multi
    def onchange_partner_id(self, part):
        res = super(SaleOrder, self).onchange_partner_id(part)
        store = False
        if part and self.env.context.get('store_id', False):
            store_id = self.env.context['store_id']
            store = self.env['sale.store'].browse(store_id)
            partner = self.env['res.partner'].browse(part)
        elif part:
            partner = self.env['res.partner'].browse(part)
            if partner.store_values:
                store = partner.store_values[0].store

        if store:
            res['value']['sale_store_id'] = store.id
            payment_mode_id = partner.get_store_value(store, 'payment.mode')
            pricelist_id = partner.get_store_value(store, 'product.pricelist')
            payment_term = partner.get_store_value(
                store, 'account.payment.term')
            if payment_mode_id:
                res['value']['payment_mode_id'] = payment_mode_id
            if pricelist_id:
                res['value']['pricelist_id'] = pricelist_id
            if payment_term:
                res['value']['payment_term'] = payment_term
        return res

    @api.onchange('sale_store_id')
    def onchange_sale_store_id(self):
        if self.partner_id and self.sale_store_id:
            payment_mode_id = self.partner_id.get_store_value(
                self.sale_store_id, 'payment.mode')
            pricelist_id = self.partner_id.get_store_value(self.sale_store_id,
                                                           'product.pricelist')
            payment_term = self.partner_id.get_store_value(
                self.sale_store_id, 'account.payment.term')
            if payment_mode_id:
                self.payment_mode_id = payment_mode_id
            if pricelist_id:
                self.pricelist_id = pricelist_id
            if payment_term:
                self.payment_term = payment_term
