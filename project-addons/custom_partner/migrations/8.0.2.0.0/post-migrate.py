# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute("""UPDATE res_partner set ship_return=asm_return""")
    cr.execute("""UPDATE sale_order set ship_return=asm_return""")
