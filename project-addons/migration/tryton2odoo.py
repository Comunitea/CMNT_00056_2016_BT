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
            self.migrate_party_party()
            #self.TAXES_MAP = loadTaxes()
            #self.TAX_CODES_MAP = loadTaxCodes()

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
        self.d[getKey(pp, 1)] = 1 # res_company

        for part_data in data:
            vals = {'ref': part_data['code'],
                    'active': part_data['active'],
                    'name': part_data['name'],
                    'comercial': part_data['trade_name'],
                    'email': part_data['esale_email'] or part_data['email'],
                    'not_in_mod347': not part_data['include_347'] and True
                    or False,
                    'vat': part_data['vat'],
                    'phone': part_data['phone'],
                    'fax': part_data['fax'],
                    'website': part_data['website'],
                    'comment': part_data['comment'],
                    'is_company': True}

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

            partner_id = self.odoo.create("res.partner", vals)
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
                vals = {'street': add['street'],
                        'streetbis': add['street2'],
                        'zip': add['zip'],
                        'city': add['city']
                }
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





Tryton2Odoo()
