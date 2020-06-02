# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos S.L
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from openerp.osv import fields, osv
from openerp import tools


class sale_report(osv.osv):
    _inherit = "sale.report"

    _columns = {
        "state_id": fields.many2one("res.country.state", "Fed. state", readonly=True)
    }

    def _select(self):
        select_str = super(sale_report, self)._select()
        this_str = """,rp.state_id"""
        return select_str + this_str

    def _from(self):
        from_str = super(sale_report, self)._from()
        this_str = " join res_partner rp on (rp.id = s.partner_id)"
        return from_str + this_str

    def _group_by(self):
        group_by_str = super(sale_report, self)._group_by()
        this_str = """,rp.state_id"""
        return group_by_str + this_str
