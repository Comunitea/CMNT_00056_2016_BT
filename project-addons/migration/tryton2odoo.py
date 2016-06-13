#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from config import Config
from odoolib import OdooConnect
import psycopg2
from psycopg2.extras import DictCursor
import shelve
from utils import *


class Tryton2Odoo(object):
    def __init__(self):
        """método incial"""
        try:
            self.odoo = OdooConnect()
            self.connOdoo = psycopg2.\
                connect("dbname='" + Config.ODOO_DATABASE +
                        "' user='" + Config.ODOO_DB_USER +
                        "' host='" + Config.ODOO_DB_HOST +
                        "' password='" + Config.ODOO_DB_PASSWORD + "'")
            self.crO = self.connOdoo.cursor(cursor_factory=DictCursor)
            self.connTryton = psycopg2.\
                connect("dbname='" + Config.TRYTON_DATABSE +
                        "' user='" + Config.TRYTON_DB_USER +
                        "' host='" + Config.TRYTON_DB_HOST +
                        "' password='" + Config.TRYTON_DB_PASSWORD + "'")
            self.crT = self.connTryton.cursor(cursor_factory=DictCursor)
            self.d = shelve.open("devel_cache_file")

            # Proceso
            #self.migrate_account_fiscalyears()
            #self.migrate_account_period()
            #self.migrate_new_accounts()
            #self.migrate_party_party()
            #self.migrate_party_category()
            #self.migrate_account_journal()
            #self.sync_banks()
            #self.migrate_bank_accounts()
            self.TAXES_MAP = loadTaxes()
            self.TAX_CODES_MAP = loadTaxCodes()
            self.PAYMENT_MODES_MAP = loadPaymentModes()
            self.migrate_account_moves()
            #self.migrate_account_reconciliation()
            #self.migrate_product_category()
            #self.migrate_product_uom()
            #self.migrate_product_product()
            #self.migrate_kits()
            self.PAYMENT_TERM_MAP = loadPaymentTerms()

            self.d.close()
            print ("Successfull migration")
        except Exception, e:
            print ("ERROR: ", (e))
            sys.exit(1)

    def migrate_account_fiscalyears(self):
        self.crT.execute("select id,code,name,end_date,company,start_date,"
                         "state from account_fiscalyear")
        data = self.crT.fetchall()
        STATES_MAP = {'open': 'draft',
                      'close': 'done'}
        tt = "account_fiscalyear"

        for year_data in data:
            vals = {'code': year_data["code"],
                    'date_stop': format_date(year_data["end_date"]),
                    'name': year_data['name'],
                    'date_start': format_date(year_data['start_date']),
                    'company_id': year_data['company'],
                    'state': STATES_MAP[year_data['state']]}
            fyear_id = self.odoo.create("account.fiscalyear", vals)
            self.d[getKey(tt, year_data["id"])] = fyear_id
        return True

    def migrate_account_period(self):
        self.crT.execute("select id,code,end_date,start_date,state,type,"
                         "fiscalyear,name from account_period")
        data = self.crT.fetchall()
        STATES_MAP = {'open': 'draft',
                      'close': 'done'}
        tt = "account_period"
        fy = "account_fiscalyear"

        for period_data in data:
            vals = {'date_stop': format_date(period_data['end_date']),
                    'code': period_data['code'],
                    'name': period_data['name'],
                    'date_start': format_date(period_data['start_date']),
                    'company_id': 1,
                    'fiscalyear_id':
                    self.d[getKey(fy, period_data["fiscalyear"])],
                    'state': STATES_MAP[period_data['state']],
                    'special': period_data['type'] == "adjustment" and True
                    or False}
            period_id = self.odoo.create("account.period", vals)
            self.d[getKey(tt, period_data["id"])] = period_id
        return True

    def migrate_new_accounts(self):
        self.crT.execute("select id,code,name from account_account where "
                         "kind != 'view'")
        data = self.crT.fetchall()
        aa = "account_account"

        for acc_data in data:
            odoo_code = tryton2odoo_account_code(acc_data["code"])
            acc_ids = self.odoo.search("account.account",
                                       [('code', '=', odoo_code)])
            if acc_ids:
                self.d[getKey(aa, acc_data["id"])] = acc_ids[0]
            else:
                parent_ids = False
                parent_account_code = odoo_code[:-1]
                while len(parent_account_code) > 0:
                    parent_ids = self.odoo.\
                        search("account.account",
                               [('code', '=', parent_account_code)])
                    if parent_ids:
                        parent_account_code = ""
                    else:
                        parent_account_code = parent_account_code[:-1]
                if parent_ids:
                    parent_data = self.odoo.read("account.account",
                                                 parent_ids[0],
                                                 ["user_type",
                                                  "child_parent_ids"])
                    acc_type = "other"
                    if parent_data['child_parent_ids']:
                        child_data = self.odoo.\
                            read("account.account",
                                 parent_data['child_parent_ids'][0],
                                 ['type'])
                        acc_type = child_data['type']
                    account_id = self.odoo.\
                        create("account.account",
                               {'code': odoo_code,
                                'name': acc_data["name"],
                                'type': acc_type,
                                'user_type': parent_data["user_type"][0],
                                'parent_id': parent_ids[0]})
                    self.d[getKey(aa, acc_data["id"])] = account_id
        return True

    def migrate_party_party(self):
        self.crT.\
            execute("select id,code,active,name,comment,trade_name,"
                    "esale_email,attributes,include_347,(select code from "
                    "party_identifier where party = party_party.id) as vat,"
                    "(select min(value) from party_contact_mechanism where "
                    "party = party_party.id and address is null and "
                    "type = 'email' and active=true) as email,(select "
                    "min(value) from party_contact_mechanism where party = "
                    "party_party.id and address is null and type = 'phone' "
                    "and active=true) as phone,(select min(value) from "
                    "party_contact_mechanism where party = party_party.id "
                    "and address is null and type = 'fax' and active=true) "
                    "as fax,(select min(value) from party_contact_mechanism "
                    "where party = party_party.id and address is null and "
                    "type = 'website' and active=true) as website from "
                    "party_party where id != 1")
        data = self.crT.fetchall()
        pp = "party_party"
        pa = "party_address"
        self.d[getKey(pp, 1)] = 1  # res_company

        for part_data in data:
            vals = {'ref': part_data['code'] or False,
                    'active': part_data['active'],
                    'name': part_data['name'],
                    'comercial': part_data['trade_name'] or False,
                    'email': part_data['esale_email'] or part_data['email']
                    or False,
                    'not_in_mod347': not part_data['include_347'] and True
                    or False,
                    'phone': part_data['phone'] or False,
                    'fax': part_data['fax'] or False,
                    'website': part_data['website'] or False,
                    'comment': part_data['comment'] or False,
                    'is_company': True}

            if part_data['attributes']:
                attributes = eval(part_data['attributes'])
                if attributes.get('medical_code', False):
                    vals['medical_code'] = attributes['medical_code']
                if attributes.get('timetable', False):
                    vals['timetable'] = attributes['timetable']

            self.crT.execute("select count(*) from sale_sale where party = %s"
                             % (part_data["id"]))
            result = self.crT.fetchone()
            if result and result["count"]:
                vals['customer'] = True

            self.crT.execute("select count(*) from purchase_purchase where "
                             "party = %s" % (part_data["id"]))
            result = self.crT.fetchone()
            if result and result["count"]:
                vals['supplier'] = True

            print "vals: ", vals
            partner_id = self.odoo.create("res.partner", vals)
            if part_data.get('vat', False):
                try:
                    self.odoo.write("res.partner", [partner_id],
                                    {'vat': part_data['vat']})
                except:
                    print "VAT not valid: ", part_data['vat']
            self.d[getKey(pp, part_data["id"])] = partner_id

            self.crT.\
                execute("select party_address.id,city,party_address.name,zip,"
                        "streetbis,street,active,party,comment_shipment,"
                        "delivery,country_country.code,(select min(value) "
                        "from party_contact_mechanism where "
                        "address=party_address.id and type = 'email' and "
                        "active=true) as email,(select min(value) from "
                        "party_contact_mechanism where "
                        "address=party_address.id and type = 'phone' and "
                        "active=true) as phone,(select min(value) from "
                        "party_contact_mechanism where "
                        "address=party_address.id and type = 'fax' "
                        "and active=true) as fax,(select min(value) "
                        "from party_contact_mechanism where "
                        "address=party_address.id and type = 'website' "
                        "and active=true) as website from party_address "
                        "left join country_country on country_country.id = "
                        "party_address.country "
                        "where party = %s order by invoice desc"
                        % (part_data["id"]))
            add_data = self.crT.fetchall()
            partner_address = False
            for add in add_data:
                vals = {'street': add['street'] or False,
                        'street2': add['streetbis'] or False,
                        'zip': add['zip'] or False,
                        'city': add['city'] or False}
                if add['code']:
                    country_ids = self.odoo.search("res.country",
                                                   [('code', '=',
                                                     add['code'])])
                    if country_ids:
                        vals['country_id'] = country_ids[0]
                        if add['code'] == "ES" and add['zip']:
                            state_ids = self.odoo.\
                                search("res.country.state",
                                       [('country_id', '=', country_ids[0]),
                                        ('code', '=', add['zip'][:2])])
                            if state_ids:
                                vals['state_id'] = state_ids[0]

                if not partner_address:
                    self.odoo.write("res.partner", [partner_id], vals)
                    partner_address = True
                    self.d[getKey(pa, add["id"])] = partner_id
                else:
                    vals.update({'parent_id': partner_id,
                                 'name': add['name'],
                                 'active': add['active'],
                                 'carrier_notes': add['comment_shipment']
                                 or False,
                                 'phone': part_data['phone'] or False,
                                 'fax': part_data['fax'] or False,
                                 'website': part_data['website'] or False,
                                 'email': part_data['email'] or False,
                                 'use_parent_address': False})
                    if add['delivery']:
                        vals['type'] = 'delivery'
                    print "vals: ", vals
                    add_id = self.odoo.create('res.partner', vals)
                    self.d[getKey(pa, add["id"])] = add_id

        return True

    def migrate_party_category(self):
        self.crT.execute("select id,name, parent,active from party_category "
                         "order by parent desc")
        data = self.crT.fetchall()
        pc = "party_category"
        pp = "party_party"
        for cat_data in data:
            vals = {'name': cat_data['name'],
                    'active': cat_data['active']}
            if cat_data.get('parent', False):
                vals['parent_id'] = self.d[getKey(pc, cat_data["parent"])]
            cat_id = self.odoo.create("res.partner.category", vals)
            self.d[getKey(pc, cat_data["id"])] = cat_id

        self.crT.execute("select category,party from party_category_rel")
        partner_data = self.crT.fetchall()
        for part_data in partner_data:
            partner_id = self.d[getKey(pp, part_data["party"])]
            category_id = self.d[getKey(pc, part_data["category"])]
            self.odoo.write("res.partner", [partner_id],
                            {'category_id': [(4, category_id)]})

        return True

    def migrate_account_journal(self):
        BY_DEFAULT_JOURNALS = {'sale': ["VEN"],
                               'cash': ["BAN1"],
                               'bank': ["BAN2"],
                               'purchase': ["COMPR"],
                               #'general': ['Vario'],
                               'general': [],
                               'situation': [],
                               'sale_refund': ["AVENT"]}
        JOURNAL_TYPE_MAP = {'revenue': ['sale', 'sale_refund'],
                            'expense': ['purchase'],
                            'cash': ['bank'],
                            'commission': ['general'],
                            'general': ['general'],
                            'situation': ['situation'],
                            'write-off': ['general']}
        self.crT.execute("select id,update_posted,code,type,name "
                         "from account_journal")
        data = self.crT.fetchall()
        aj = "account_journal"
        ajr = "account_journal_refund"
        tt = "account_fiscalyear"
        first_journal_id = self.odoo.search("account.journal", [])[0]
        first_journal_data = self.odoo.read("account.journal",
                                            first_journal_id,
                                            ['sequence_id'])
        journal_seq_id = first_journal_data['sequence_id'][0]

        for journal_data in data:
            journal_id = False
            vals = {
                'name': journal_data['name'],
                'update_posted': journal_data['update_posted'],
                'sequence_id': journal_seq_id,
                'code': journal_data['code'],
            }
            if journal_data['name'] == "Cash":
                vals['type'] = "cash"
            elif len(JOURNAL_TYPE_MAP[journal_data['type']]) == 1:
                vals['type'] = JOURNAL_TYPE_MAP[journal_data['type']][0]

            if vals.get('type', False):
                if BY_DEFAULT_JOURNALS[vals['type']]:
                    journal_code = \
                        BY_DEFAULT_JOURNALS[vals['type']].pop()
                    journal_id = self.odoo.search("account.journal",
                                                  [('code', '=',
                                                    journal_code)])[0]
                if journal_id:
                    print "write vals: ", vals
                    self.odoo.write("account.journal", [journal_id],
                                    vals)
                    self.d[getKey(aj, journal_data["id"])] = journal_id
                else:
                    print "create vals: ", vals
                    journal_id = self.odoo.create("account.journal", vals)
                    self.d[getKey(aj, journal_data["id"])] = journal_id
            else:
                self.crT.\
                    execute("select fiscalyear,out_iss.name "
                            "as out_name,out_iss.number_next_internal as "
                            "out_number_next,out_iss.padding as out_padding,"
                            "out_iss.number_increment as out_increment,"
                            "out_iss.prefix as out_prefix,ref_iss.name as "
                            "ref_name,ref_iss.number_next_internal as "
                            "ref_number_next,ref_iss.padding as ref_padding,"
                            "ref_iss.number_increment as ref_increment,"
                            "ref_iss.prefix as ref_prefix from "
                            "account_journal_invoice_sequence inner join "
                            "ir_sequence_strict out_iss on out_iss.id = "
                            "out_invoice_sequence inner join "
                            "ir_sequence_strict ref_iss on ref_iss.id = "
                            "out_credit_note_sequence where journal = %s "
                            "order by fiscalyear asc"
                            % (journal_data["id"]))
                seq_data = self.crT.fetchall()
                out_invoice_seq = False
                out_refund_seq = False
                for jtype in JOURNAL_TYPE_MAP[journal_data['type']]:
                    vals['type'] = jtype
                    journal_id = False
                    if jtype == "sale":
                        m = aj
                        if out_invoice_seq:
                            vals['invoice_sequence_id'] = out_invoice_seq
                        else:
                            for seq in seq_data:
                                svals = {'name': seq['out_name'],
                                         'implementation': 'no_gap',
                                         'prefix': seq['out_prefix'],
                                         'padding': seq['out_padding'],
                                         'number_next_actual':
                                         seq['out_number_next'],
                                         'number_increment':
                                         seq['out_increment']}

                                seq_id = self.odoo.\
                                    create("ir.sequence", svals)
                                if not out_invoice_seq:
                                    out_invoice_seq = seq_id
                                    vals['invoice_sequence_id'] = \
                                        out_invoice_seq
                                else:
                                    year_seq = self.odoo.\
                                        create("ir.sequence", svals)
                                    self.odoo.\
                                        create("account.sequence.fiscalyear",
                                               {'sequence_id': year_seq,
                                                'fiscalyear_id':
                                                self.
                                                d[getKey(tt,
                                                         seq["fiscalyear"])],
                                                'sequence_main_id':
                                                out_invoice_seq})
                    elif jtype == "sale_refund":
                        m = ajr
                        vals['code'] = u"A" + vals['code']
                        vals['name'] = u"Ab. " + vals['name']
                        if out_refund_seq:
                            vals['invoice_sequence_id'] = out_refund_seq
                        else:
                            for seq in seq_data:
                                svals = {'name': seq['ref_name'],
                                         'implementation': 'no_gap',
                                         'prefix': seq['ref_prefix'],
                                         'padding': seq['ref_padding'],
                                         'number_next_actual':
                                         seq['ref_number_next'],
                                         'number_increment':
                                         seq['ref_increment']}

                                seq_id = self.odoo.\
                                    create("ir.sequence", svals)
                                if not out_refund_seq:
                                    out_refund_seq = seq_id
                                    vals['invoice_sequence_id'] = \
                                        out_refund_seq
                                else:
                                    year_seq = self.odoo.\
                                        create("ir.sequence", svals)
                                    self.odoo.\
                                        create("account.sequence.fiscalyear",
                                               {'sequence_id': year_seq,
                                                'fiscalyear_id':
                                                self.
                                                d[getKey(tt,
                                                         seq["fiscalyear"])],
                                                'sequence_main_id':
                                                out_refund_seq})
                    if BY_DEFAULT_JOURNALS[vals['type']]:
                        journal_code = \
                            BY_DEFAULT_JOURNALS[vals['type']].pop()
                        journal_id = self.odoo.search("account.journal",
                                                      [('code', '=',
                                                        journal_code)])[0]
                    if journal_id:
                        print "write vals: ", vals
                        self.odoo.write("account.journal", [journal_id],
                                        vals)
                        self.d[getKey(m, journal_data["id"])] = journal_id
                    else:
                        print "create vals: ", vals
                        journal_id = self.odoo.create("account.journal", vals)
                        self.d[getKey(m, journal_data["id"])] = journal_id
        return True

    def sync_banks(self):
        self.crT.execute("select id,bank_code,bic,party from bank")
        data = self.crT.fetchall()
        pp = "party_party"
        bnk = "bank"
        for bnk_data in data:
            bank_ids = self.odoo.search("res.bank", [('code', '=',
                                                      bnk_data['bank_code'])])
            if bank_ids:
                self.d[getKey(bnk, bnk_data["id"])] = bank_ids[0]
            else:
                partner_id = self.d[getKey(pp, bnk_data["party"])]
                if partner_id:
                    partner_data = self.odoo.\
                        read("res.partner", partner_id,
                             ['name', 'street', 'street2', 'zip', 'city',
                              'state_id', 'country_id', 'phone', 'fax',
                              'email', 'website', 'vat'])
                    vals = {
                        'name': partner_data['name'],
                        'street': partner_data['street'],
                        'street2': partner_data['street2'],
                        'zip': partner_data['zip'],
                        'city': partner_data['city'],
                        'state': partner_data['state_id'] and
                        partner_data['state_id'][0] or False,
                        'country': partner_data['country_id'] and
                        partner_data['country_id'][0] or False,
                        'phone': partner_data['phone'],
                        'fax': partner_data['fax'],
                        'email': partner_data['email'],
                        'vat': partner_data['vat'],
                        'code': bnk_data['bank_code'],
                        'bic': (bnk_data['bic'] and bnk_data['bic'] != "")
                        and bnk_data['bic'] or False}
                    bank_id = self.odoo.create("res.bank", vals)
                    self.d[getKey(bnk, bnk_data["id"])] = bank_id

        return True

    def migrate_bank_accounts(self):
        self.crT.execute("select bank_account.id,bank,active,owner,type,"
                         "number from \"bank_account-party_party\" bapp "
                         "inner join bank_account on bapp.account = "
                         "bank_account.id inner join bank_account_number on "
                         "bank_account_number.account = bank_account.id")
        data = self.crT.fetchall()
        pp = "party_party"
        bnk = "bank"
        ba = "bank_account"
        for acc_data in data:
            bank_id = self.d[getKey(bnk, acc_data["bank"])]
            bank_data = self.odoo.read("res.bank", bank_id,
                                       ['country', 'name', 'bic'])
            owner_id = self.d[getKey(pp, acc_data["owner"])]
            owner_data = self.odoo.read("res.partner", owner_id,
                                        ['name', 'street', 'zip', 'city',
                                         'state_id', 'country_id'])
            vals = {
                'state': acc_data['type'] == 'other' and 'bank' or
                acc_data['type'],
                'acc_number': acc_data['number'],
                'acc_country_id': bank_data['country'] and
                bank_data['country'][0] or False,
                'bank': bank_id,
                'bank_name': bank_data['name'],
                'bank_bic': bank_data['bic'] or False,
                'active': acc_data['active'],
                'partner_id': owner_id,
                'owner_name': owner_data['name'],
                'street': owner_data['street'],
                'zip': owner_data['zip'],
                'city': owner_data['city'],
                'state_id': owner_data['state_id'] and
                owner_data['state_id'][0] or False,
                'country_id': owner_data['country_id'] and
                owner_data['country_id'][0] or False,
            }
            acc_id = self.odoo.create("res.partner.bank", vals)
            self.d[getKey(ba, acc_data["id"])] = acc_id

        return True

    def migrate_account_moves(self):
        self.crT.execute("select id,post_number,journal,period,date,state,"
                         "description from account_move")
        data = self.crT.fetchall()
        am = "account_move"
        aml = "account_move_line"
        aj = "account_journal"
        ap = "account_period"
        pp = "party_party"
        aa = "account_account"
        for move_data in data:
            if self.d.has_key(getKey(am, move_data["id"])):
                move_ids = self.odoo.\
                    search("account.move",
                           [('id', '=', self.d[getKey(am, move_data["id"])])])
                if move_ids:
                    continue
            period_id = self.d[getKey(ap, move_data["period"])]
            journal_id = self.d[getKey(aj, move_data["journal"])]
            vals = {
                'journal_id': journal_id,
                'period_id': period_id,
                'ref': move_data['description'] or "",
                'date': format_date(move_data['date']),
                'name': move_data['post_number'] or "/"
            }
            print "vals: ", vals
            move_id = self.odoo.create("account.move", vals)
            self.d[getKey(am, move_data["id"])] = move_id
            self.crT.execute("select aml.id,debit,description,account,credit,"
                             "party,maturity_date,payment_type,"
                             "atl.code as tax_code,atl.amount as tax_amount "
                             "from account_move_line aml left join "
                             "account_tax_line atl on atl.move_line = "
                             "aml.id where move = %s"
                             % (move_data["id"]))
            line_data = self.crT.fetchall()
            for line in line_data:
                partner_id = False
                if line['party']:
                    partner_id = self.d[getKey(pp, line["party"])]
                account_id = self.d[getKey(aa, line["account"])]
                tax_code_id = False
                if line['tax_code']:
                    tax_code_id = self.TAX_CODES_MAP[str(line['tax_code'])]

                lines_vals = {'name': line['description'] or "-",
                              'journal_id': journal_id,
                              'period_id': period_id,
                              'partner_id': partner_id,
                              'account_id': account_id,
                              'debit': float(line['debit']),
                              'credit': float(line['credit']),
                              'date': format_date(move_data['date']),
                              'date_maturity': line['maturity_date'] and
                              format_date(line['maturity_date']) or False,
                              'move_id': move_id,
                              'tax_code_id': tax_code_id,
                              'tax_amount': line['tax_amount'] and
                              float(line['tax_amount']) or 0.0}
                if lines_vals['debit'] and lines_vals['debit'] < 0:
                    lines_vals['credit'] = abs(lines_vals['debit'])
                    lines_vals['debit'] = 0.0
                elif lines_vals['credit'] and lines_vals['credit'] < 0:
                    lines_vals['debit'] = abs(lines_vals['credit'])
                    lines_vals['credit'] = 0.0
                update = True
                if self.d.has_key(getKey(aml, line["id"])):
                    line_ids = self.odoo.\
                        search("account.move.line",
                               [('id', '=', self.d[getKey(aml, line["id"])])])
                    if line_ids:
                        lines_vals['debit'] = 0.0
                        lines_vals['credit'] = 0.0
                        update = False
                print "lines_vals: ", lines_vals
                move_line_id = self.odoo.create("account.move.line",
                                                lines_vals)
                if update:
                    self.d[getKey(aml, line["id"])] = move_line_id

            if move_data['state'] == "posted":
                self.odoo.execute("account.move", "post", [move_id])
                print "POST"
        return True

    def migrate_account_reconciliation(self):
        self.crT.execute("select id,name from account_move_reconciliation")
        data = self.crT.fetchall()
        amr = "account_move_reconciliation"
        aml = "account_move_line"
        for rec in data:
            vals = {
                'name': rec['name'],
                'type': 'auto'
            }
            rec_id = self.odoo.create("account.move.reconcile", vals)
            self.d[getKey(amr, rec["id"])] = rec_id

            self.crT.execute("select id from account_move_line where "
                             "reconciliation = %s" % (rec['id']))
            lines_data = self.crT.fetchall()
            for line in lines_data:
                move_line_id = self.d[getKey(aml, line["id"])]
                self.odoo.write("account.move.line", [move_line_id],
                                {'reconcile_id': rec_id})
        return True

    def migrate_product_category(self):
        self.crT.execute("select id,name,parent from product_category order "
                         "by parent asc nulls first")
        data = self.crT.fetchall()
        pc = "product_category"
        for cat in data:
            parent_id = False
            if cat['parent']:
                parent_id = self.d[getKey(pc, cat["id"])]
            vals = {'name': cat['name'],
                    'parent_id': parent_id,
                    'type': 'normal'}
            cat_id = self.odoo.create("product.category", vals)
            self.d[getKey(pc, cat["id"])] = cat_id
        return True

    def migrate_product_uom(self):
        UOM_CAT_MAP = {'1': 1,  # Unidades
                       '2': 2,  # Peso
                       '3': 3,  # Horario
                       '4': 4,  # Longitud
                       '5': 5,  # Volumen
                       '6': 6}  # Superficie (Hay que crearla)
        UOM_MAP = loadProductUoms()
        self.crT.execute("select id,name,category,rounding,rate,active from "
                         "product_uom")
        data = self.crT.fetchall()
        pu = "product_uom"
        for uom_data in data:
            if str(uom_data['id']) in UOM_MAP:
                self.d[getKey(pu, uom_data["id"])] = \
                    UOM_MAP[str(uom_data['id'])]
            else:
                vals = {
                    'name': uom_data['name'],
                    'category_id': UOM_CAT_MAP[str(uom_data['category'])],
                    'rounding': float(uom_data['rounding']),
                    'factor': float(uom_data['rate']),
                    'active': uom_data['active'],
                    'uom_type': uom_data['rate'] > 1 and 'smaller' or
                    (uom_data['rate'] == 1 and 'reference' or
                     uom_data['rate'] < 1 and 'bigger' or 'reference')
                }
                uom_id = self.odoo.create("product.uom", vals)
                self.d[getKey(pu, uom_data["id"])] = uom_id
        return True

    def migrate_product_product(self):
        self.crT.\
            execute("select pp.id,category,name,default_uom,pp.active,"
                    "consumable,type,purchasable,purchase_uom,salable,"
                    "sale_uom,delivery_time,base_code,weight_uom,"
                    "kit_fixed_list_price,kit,pt.id as template_id,"
                    "stock_depends_on_kit_components,number,taxes_category "
                    "from product_product pp inner join product_template pt "
                    "on pt.id = pp.template left join product_code pc on "
                    "pc.product = pp.id and barcode='EAN' and "
                    "pc.active = true")
        data = self.crT.fetchall()
        pc = "product_category"
        pp = "product_product"
        pu = "product_uom"
        at = "account_tax"
        aa = "account_account"
        account_expense_field = False
        account_incoming_field = False
        cost_method_field = False
        list_price_field = False
        cost_price_field = False
        for prod in data:
            categ_id = self.d[getKey(pc, prod["category"])]
            default_uom_id = self.d[getKey(pu, prod["default_uom"])]
            purchase_uom_id = self.d[getKey(pu, prod["purchase_uom"])]
            vals = {'name': prod['name'],
                    'uom_id': default_uom_id,
                    'active': prod['active'],
                    'type': prod['type'] != "goods" and prod['type'] or
                    (prod['consumable'] and 'consu' or 'product'),
                    'purchase_ok': prod['purchasable'],
                    'uom_po_id': purchase_uom_id,
                    'sale_ok': prod['salable'],
                    'pack_fixed_price': prod['kit_fixed_list_price'],
                    'sale_delay': prod['delivery_time'] and
                    float(prod['delivery_time']) or 0,
                    'default_code': prod['base_code'],
                    'weight': prod['weight_uom'] and float(prod['weight_uom'])
                    or 0.0,
                    'stock_depends': prod['stock_depends_on_kit_components'],
                    'ean13': prod['number'] or False,
                    'categ_id': categ_id}
            if prod['taxes_category']:
                self.crT.execute("select tax from "
                                 "product_category_customer_taxes_rel "
                                 "where category = %s" % (prod["category"]))
                tax_data = self.crT.fetchall()
                taxes_ids = []
                for tax in tax_data:
                    tax_id = self.d[getKey(at, tax["tax"])]
                    taxes_ids.append(tax_id)
                if taxes_ids:
                    vals['taxes_id'] = [(6, 0, taxes_ids)]
                self.crT.execute("select tax from "
                                 "product_category_supplier_taxes_rel "
                                 "where category = %s" % (prod["category"]))
                tax_data = self.crT.fetchall()
                taxes_ids = []
                for tax in tax_data:
                    tax_id = self.d[getKey(at, tax["tax"])]
                    taxes_ids.append(tax_id)
                if taxes_ids:
                    vals['supplier_taxes_id'] = [(6, 0, taxes_ids)]
            else:
                self.crT.execute("select tax from "
                                 "product_customer_taxes_rel "
                                 "where product = %s" % (prod["template_id"]))
                tax_data = self.crT.fetchall()
                taxes_ids = []
                for tax in tax_data:
                    tax_id = self.d[getKey(at, tax["tax"])]
                    taxes_ids.append(tax_id)
                if taxes_ids:
                    vals['taxes_id'] = [(6, 0, taxes_ids)]
                self.crT.execute("select tax from "
                                 "product_supplier_taxes_rel "
                                 "where product = %s" % (prod["template_id"]))
                tax_data = self.crT.fetchall()
                taxes_ids = []
                for tax in tax_data:
                    tax_id = self.d[getKey(at, tax["tax"])]
                    taxes_ids.append(tax_id)
                if taxes_ids:
                    vals['supplier_taxes_id'] = [(6, 0, taxes_ids)]

            #Propiedades
            #Cost method
            if not cost_method_field:
                self.crT.execeute("select id from ir_model_field where name = "
                                  "'cost_price_method' and module = 'product'")
                field = self.crT.fetchone()
                cost_method_field = field['id']
            self.crT.execute("select value from ir_property where field = %s "
                             "and res = 'product.template,%s' limit 1"
                             % (cost_method_field, prod["template_id"]))
            field_value = self.crT.fetchone()
            if field_value:
                field_value = field_value.replace(",", "")
                vals['cost_method'] = field_value == 'fixed' and 'standard' \
                    or field_value
            # list_price
            if not list_price_field:
                self.crT.execeute("select id from ir_model_field where name = "
                                  "'list_price' and module = 'product'")
                field = self.crT.fetchone()
                list_price_field = field['id']
            self.crT.execute("select value from ir_property where field = %s "
                             "and res = 'product.template,%s' limit 1"
                             % (list_price_field, prod["template_id"]))
            field_value = self.crT.fetchone()
            if field_value:
                field_value = field_value.replace(",", "")
                vals['list_price'] = float(field_value)
            # cost_price
            if not cost_price_field:
                self.crT.execeute("select id from ir_model_field where name = "
                                  "'cost_price' and module = 'product'")
                field = self.crT.fetchone()
                cost_price_field = field['id']
            self.crT.execute("select value from ir_property where field = %s "
                             "and res = 'product.template,%s' limit 1"
                             % (cost_price_field, prod["template_id"]))
            field_value = self.crT.fetchone()
            if field_value:
                field_value = field_value.replace(",", "")
                vals['standard_price'] = float(field_value)
            # account_expense
            if not account_expense_field:
                self.crT.execeute("select id from ir_model_field where name = "
                                  "'account_expense' and module = "
                                  "'account_product'")
                field = self.crT.fetchone()
                account_expense_field = field['id']
            self.crT.execute("select value from ir_property where field = %s "
                             "and res = 'product.template,%s' limit 1"
                             % (account_expense_field, prod["template_id"]))
            field_value = self.crT.fetchone()
            if field_value:
                field_value = field_value.split(",")[1]
                account_id = self.d[getKey(aa, int(field_value))]
                vals['property_account_expense'] = account_id
            # account_revenue
            if not account_incoming_field:
                self.crT.execeute("select id from ir_model_field where name = "
                                  "'account_revenue' and module = "
                                  "'account_product'")
                field = self.crT.fetchone()
                account_incoming_field = field['id']
            self.crT.execute("select value from ir_property where field = %s "
                             "and res = 'product.template,%s' limit 1"
                             % (account_incoming_field, prod["template_id"]))
            field_value = self.crT.fetchone()
            if field_value:
                field_value = field_value.split(",")[1]
                account_id = self.d[getKey(aa, int(field_value))]
                vals['property_account_income'] = account_id

            prod_id = self.odoo.create("product.product", vals)
            self.d[getKey(pp, prod["id"])] = prod_id
        return True

    def migrate_kits(self):
        self.crT.execute("select parent,product,quantity from "
                         "product_kit_line")
        kit_data = self.crT.fetchall()
        pp = "product_product"
        for kit_line in kit_data:
            lin_prod_id = self.d[getKey(pp, kit_line["product"])]
            kit_prod_id = self.d[getKey(pp, kit_line["parent"])]
            vals = {'quantity': float(kit_data['quantity']),
                    'product_id': lin_prod_id,
                    'parent_product_id': kit_prod_id}
            self.odoo.create("product.pack.line", vals)
        return True

Tryton2Odoo()
