# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ResPartner(models.Model):

    _inherit = 'res.partner'

    timetable = fields.Text("Timetable")
    medical_code = fields.Char("Medical code", size=32)
    carrier_service_id = fields.Many2one("carrier.api.service",
                                         "Carrier service")
    ship_return = fields.Boolean("return")
    carrier_notes = fields.Text("Carrier notes")

    @api.onchange('medical_code')
    def on_change_medical_code(self):
        if self.medical_code and len(self.medical_code) <= 8:
            code_search = self.medical_code[:3] + "-0000"
            if code_search != self.medical_code:
                partners = self.search([('medical_code', '=', code_search)])
                if partners:
                    agent_ids = [partners[0].id]
                    if partners[0].agents:
                        agent_ids.\
                            extend([x.id for x in partners[0].agents])
                    self.agents = [(6, 0, agent_ids)]
                    if partners[0].user_id:
                        self.user_id = partners[0].user_id.id

    @api.model
    def create(self, vals):
        obj = super(ResPartner, self).create(vals)
        if (not vals.get('agents', False) or not vals['agents'][0][2]) and \
                vals.get('medical_code', False):
            obj.on_change_medical_code()
        return obj

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            if record.parent_id and not record.is_company and \
                    not record.use_parent_address and record.street:
                name = "%s, %s" % (name, record.street)
            elif record.parent_id and not record.is_company:
                name = "%s, %s" % (record.parent_name, name)
            if context.get('show_address_only'):
                name = self._display_address(cr, uid, record, without_company=True, context=context)
            if context.get('show_address'):
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
            name = name.replace('\n\n','\n')
            name = name.replace('\n\n','\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            res.append((record.id, name))
        return res
