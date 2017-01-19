# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, tools, api


class commission_report(models.Model):

    _name = "commission.report"
    _description = "Sale commission report"
    _auto = False

    product_id = fields.Many2one('product.product', 'Product')
    agent_id = fields.Many2one('res.partner', 'Agent')
    qty = fields.Float('Quantity')
    settled = fields.Boolean('Settled')
    inv_date = fields.Date('Date invoice')
    partner_id = fields.Many2one("res.partner", "Customer")

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT c_line.id,
                i_line.product_id  AS product_id,
                c_line.agent  AS agent_id,
                c_line.amount  AS qty,
                c_line.settled  AS settled,
                inv.date_invoice  AS inv_date,
                inv.state  AS state,
                inv.partner_id as partner_id
            FROM account_invoice_line AS i_line
                JOIN account_invoice_line_agent  AS c_line ON i_line.id=c_line.invoice_line
                JOIN account_invoice  AS inv ON i_line.invoice_id=inv.id
            WHERE inv.state IN ('open', 'paid')
            GROUP BY i_line.product_id, c_line.agent, c_line.amount, c_line.settled, inv.date_invoice, inv.state, c_line.id, inv.partner_id
        )""" % (self._table,))


class particular_report(models.AbstractModel):
	_name = 'report.commission_report.commission_report_document'
	
	@api.multi
	def render_html(self, data=None):		
		report_obj = self.env['report']
		report = report_obj._get_report_from_name('commission_report.commission_report_document')  

		# import ipdb; ipdb.set_trace()

		commission_settlement = {}
		facturasComisionistas4 = {}
		desglosePorComision = {}
		for docu in self.env[report.model].browse(self._ids):
			dic3 = {}
			dic_perc = {}
			# import ipdb; ipdb.set_trace()
			settlement = self.env['sale.commission.settlement'].search([('invoice', '=', docu.id)]) # unha factura de comisionista ten un commission.settlement
			commission_settlement[docu.id] = settlement
			
			default_commission = 0.0
			
			for plan_l in settlement.agent.plan.lines:  # creo o diccionario de porcentaxes de comisi´ons 
				commission_perc = plan_l.commission.fix_qty
				dic_perc[commission_perc] = 0.0
				if not plan_l.product:
					default_commission = commission_perc
				

			for sett_line in settlement.lines:  # para cada liña do asentamento					
				
				plan_line = self.env['sale.agent.plan.line'].search([('product', '=', sett_line.invoice_line.product_id.id),('plan', '=', sett_line.agent.plan.id)])						
				ventas = (self.env['account.invoice.line'].search([('id', '=', sett_line.invoice_line.id)])).price_subtotal
				
				if plan_line:  # se o producto est´a en sale.agent.plan.line
					commission_percentage = plan_line.commission.fix_qty
					dic_perc[commission_percentage] += ventas
				else:  # PRODUCTO QUE NON APARECE EN sale.agent.plan.line'
					dic_perc[default_commission] += ventas

				# print 'dic_perc: =================', dic_perc







				if sett_line.invoice.partner_id.commercial_partner_id not in dic3: # se o cliente non esta,
					dic3[sett_line.invoice.partner_id.commercial_partner_id]={sett_line.invoice: {}} # engade cliente e factura
				if sett_line.invoice not in dic3[sett_line.invoice.partner_id.commercial_partner_id]: # se a factura non esta
					dic3[sett_line.invoice.partner_id.commercial_partner_id][sett_line.invoice] = {} 
				# print "----------currency_id.symbol:-----------------",sett_line.invoice.currency_id.symbol
				# print "line: ", sett_line.invoice.number
				if sett_line.invoice_line.product_id not in dic3[sett_line.invoice.partner_id.commercial_partner_id][sett_line.invoice]: # se o producto non esta 
					# print "if: ", sett_line.invoice_line.product_id.name
					dic3[sett_line.invoice.partner_id.commercial_partner_id][sett_line.invoice][sett_line.invoice_line.product_id] = sett_line.settled_amount
					# print "res: ", dic3[sett_line.invoice.partner_id.commercial_partner_id][sett_line.invoice] 				
				else: # o producto si que esta 
					# print "else: ", sett_line.invoice_line.product_id.name
					dic3[sett_line.invoice.partner_id.commercial_partner_id][sett_line.invoice][sett_line.invoice_line.product_id] += sett_line.settled_amount
					# print "res: ", dic3[sett_line.invoice.partner_id.commercial_partner_id][sett_line.invoice] 				
					
				
				# print "dic3__________________: ", dic3
			
			
				
			# import ipdb; ipdb.set_trace()		
			facturasComisionistas4[docu.id] = dic3
			desglosePorComision[docu.id] = dic_perc
		# print "facturasComisionistas4: ", facturasComisionistas4






		docargs = {
			'doc_ids': self._ids,
			'doc_model': report.model,
			'docs': self.env['account.invoice'].browse(self._ids),
			'facturasComisionistas4': facturasComisionistas4,
			'commission_settlement': commission_settlement,
			'desglosePorComision': desglosePorComision,
			}
		return report_obj.render('commission_report.commission_report_document', docargs)





