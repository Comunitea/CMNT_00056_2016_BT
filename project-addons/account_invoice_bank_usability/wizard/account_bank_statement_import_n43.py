# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import models


class AccountBankStatementImport(models.TransientModel):

    _inherit = 'account.bank.statement.import'

    def _process_record_22(self, line):
        st_line = super(AccountBankStatementImport, self).\
            _process_record_22(line)
        fecha_valor = st_line['fecha_valor']
        fecha_oper = st_line['fecha_oper']
        st_line['fecha_valor'] = fecha_oper
        st_line['fecha_oper'] = fecha_valor

        return st_line
