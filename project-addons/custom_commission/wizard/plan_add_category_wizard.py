# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class AgentPlanAddProductCategory(models.TransientModel):

    _name = 'agent.plan.add.category'

    category = fields.Many2one('product.category')
    commission = fields.Many2one('sale.commission')

    @api.multi
    def add_category(self):
        plan_id = self.env.context.get('active_id')
        plan = self.env['sale.agent.plan'].browse(plan_id)
        products = self.env['product.product'].search(
            [('categ_id', '=', self.category.id)])
        plan_products = plan.mapped('lines.product')
        for product in products:
            line = self.env['sale.agent.plan.line'].search(
                [('product', '=', product.id), ('plan', '=', plan.id)])
            if line:
                line.commission = self.commission
            else:
                self.env['sale.agent.plan.line'].create(
                    {'product': product.id, 'commission': self.commission.id,
                     'plan': plan.id})
