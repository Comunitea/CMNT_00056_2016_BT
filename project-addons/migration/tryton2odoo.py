#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from config import Config
from odoolib import OdooConnect
import psycopg2
from psycopg2.extras import DictCursor
import shelve
from utils import *
import yaml
import base64
from itertools import *
from datetime import datetime


class Tryton2Odoo(object):
    def close_crO(self):
        self.connOdoo.commit()
        self.connOdoo.close()
        self.connOdoo = psycopg2.connect(
            "dbname='"
            + Config.ODOO_DATABASE
            + "' user='"
            + Config.ODOO_DB_USER
            + "' host='"
            + Config.ODOO_DB_HOST
            + "' password='"
            + Config.ODOO_DB_PASSWORD
            + "'"
        )
        self.crO = self.connOdoo.cursor(cursor_factory=DictCursor)

    def __init__(self):
        """método incial"""
        try:
            self.odoo = OdooConnect()
            # ~ self.connOdoo = psycopg2.\
            # ~ connect("dbname='" + Config.ODOO_DATABASE +
            # ~ "' user='" + Config.ODOO_DB_USER +
            # ~ "' host='" + Config.ODOO_DB_HOST +
            # ~ "' password='" + Config.ODOO_DB_PASSWORD + "'")
            # ~ self.crO = self.connOdoo.cursor(cursor_factory=DictCursor)
            self.connTryton = psycopg2.connect(
                "dbname='"
                + Config.TRYTON_DATABSE
                + "' user='"
                + Config.TRYTON_DB_USER
                + "' host='"
                + Config.TRYTON_DB_HOST
                + "' password='"
                + Config.TRYTON_DB_PASSWORD
                + "'"
            )
            self.crT = self.connTryton.cursor(cursor_factory=DictCursor)
            self.d = shelve.open("devel_cache_file")
            self.esale = True
            if len(sys.argv) > 1:
                last_update_str = sys.argv[1]
                self.last_update = datetime.strptime(
                    last_update_str, "%Y-%m-%d %H:%M:%S"
                )

            elif self.d.has_key("last_update"):
                self.last_update = self.d["last_update"]
            else:
                print ("Sin última fecha de actualización se usa hoy.")
                self.last_update = datetime.utcnow()
            # Proceso
            # self.migrate_account_fiscalyears()
            # self.migrate_account_period()
            # self.migrate_new_accounts() # ACUMULATIVO
            # self.migrate_party_party() # ACUMULATIVO
            # self.migrate_party_category() # ACUMULATIVO
            # self.migrate_account_journal()
            # self.sync_banks() # ACUMULATIVO
            # self.migrate_bank_accounts() # ACUMULATIVO
            self.TAXES_MAP = loadTaxes()
            self.TAX_CODES_MAP = loadTaxCodes()
            self.PAYMENT_MODES_MAP = loadPaymentModes()
            self.FISCAL_POSITIONS_MAP = loadFiscalPositions()
            # self.migrate_account_moves() # ACUMULATIVO
            # self.migrate_account_reconciliation()  # ACUMULATIVO
            # self.migrate_product_category() # ACUMULATIVO
            self.UOM_MAP = loadProductUoms()
            # self.migrate_product_uom() # ACUMULATIVO
            # self.migrate_product_product() # ACUMULATIVO
            # if self.esale:
            #    self.migrate_magento_metadata()
            #    self.migrate_prestashop_metadata()
            #    self.migrate_magento_payment_mode() # ACUMULATIVO
            self.PAYMENT_TERM_MAP = loadPaymentTerms()
            # self.migrate_invoices() #ACUMULATIVO
            # self.migrate_account_bank_statements() #ACUMULATIVO
            self.LOCATIONS_MAP = loadStockLocations()
            # self.migrate_stock_lots() # ACUMULATIVO
            # self.migrate_inventories() # ACUMULATIVO
            # self.migrate_moves() # ACUMULATIVO
            # self.merge_quants()
            # self.migrate_pickings() #ACUMULATIVO
            # self.migrate_orderpoints() # ACUMULATIVO
            # self.migrate_carrier() #ACUMULATIVO
            # if self.esale:
            #    self.migrate_carrier_api() #ACUMULATIVO
            #    self.migrate_carrier_api_services() # ACUMULATIVO
            #    self.migrate_carrier_data() # ACUMULATIVO
            #    self.migrate_magento_carrier() # ACUMULATIVO
            # self.migrate_commission_plan() # ACUMULATIVO
            # self.migrate_commission_agent() # ACUMULATIVO
            # self.migrate_users() # ACUMULATIVO
            self.GROUPS_MAP = loadGroups()
            # self.migrate_groups()  # ACUMULATIVO
            # self.migrate_product_suppliers() # ACUMULATIVO
            # self.migrate_pricelist() # ACUMULATIVO
            # if self.esale:
            #    self.sync_ecommerce_shops() # ACUMULATIVO
            # else:
            #    self.sync_shops() # ACUMULATIVO
            # self.migrate_sales()  # ACUMULATIVO
            # self.migrate_sale_invoice_link()  # ACUMULATIVO
            # self.migrate_purchase_order()  # ACUMULATIVO
            # self.fix_product_migration()
            # self.fix_party_migration()
            # self.fix_lot_migration()
            # self.fix_product_ean14_migration()
            # self.fix_partner_payment_data()
            # self.reimport_medical_code() # Corregido migrate_party_party esta función es innecesaria
            self.fix_product_name_migration()
            print ("Nueva fecha de última actualización: %s" % str(datetime.utcnow()))
            self.d["last_update"] = datetime.utcnow()
            self.d.close()
            print ("Successfull migration")
        except Exception, e:
            print ("ERROR: ", (e))
            sys.exit(1)

    def migrate_account_fiscalyears(self):
        self.crT.execute(
            "select id,code,name,end_date,company,start_date,"
            "state from account_fiscalyear"
        )
        data = self.crT.fetchall()
        STATES_MAP = {"open": "draft", "close": "done"}
        tt = "account_fiscalyear"

        for year_data in data:
            vals = {
                "code": year_data["code"],
                "date_stop": format_date(year_data["end_date"]),
                "name": year_data["name"],
                "date_start": format_date(year_data["start_date"]),
                "company_id": year_data["company"],
                "state": STATES_MAP[year_data["state"]],
            }
            fyear_id = self.odoo.create("account.fiscalyear", vals)
            self.d[getKey(tt, year_data["id"])] = fyear_id
        return True

    def migrate_account_period(self):
        self.crT.execute(
            "select id,code,end_date,start_date,state,type,"
            "fiscalyear,name from account_period"
        )
        data = self.crT.fetchall()
        STATES_MAP = {"open": "draft", "close": "done"}
        tt = "account_period"
        fy = "account_fiscalyear"

        for period_data in data:
            vals = {
                "date_stop": format_date(period_data["end_date"]),
                "code": period_data["code"],
                "name": period_data["name"],
                "date_start": format_date(period_data["start_date"]),
                "company_id": 1,
                "fiscalyear_id": self.d[getKey(fy, period_data["fiscalyear"])],
                "state": STATES_MAP[period_data["state"]],
                "special": period_data["type"] == "adjustment" and True or False,
            }
            period_id = self.odoo.create("account.period", vals)
            self.d[getKey(tt, period_data["id"])] = period_id
        return True

    def migrate_new_accounts(self):
        self.crT.execute(
            "select id,code,name from account_account where " "kind != 'view'"
        )
        data = self.crT.fetchall()
        aa = "account_account"

        for acc_data in data:
            odoo_code = tryton2odoo_account_code(acc_data["code"])
            acc_ids = self.odoo.search("account.account", [("code", "=", odoo_code)])
            if acc_ids:
                print "Acc. exists: ", odoo_code
                self.d[getKey(aa, acc_data["id"])] = acc_ids[0]
            else:
                print "New account: ", odoo_code
                parent_ids = False
                parent_account_code = odoo_code[:-1]
                while len(parent_account_code) > 0:
                    parent_ids = self.odoo.search(
                        "account.account", [("code", "=", parent_account_code)]
                    )
                    if parent_ids:
                        parent_account_code = ""
                    else:
                        parent_account_code = parent_account_code[:-1]
                if parent_ids:
                    parent_data = self.odoo.read(
                        "account.account",
                        parent_ids[0],
                        ["user_type", "child_parent_ids"],
                    )
                    acc_type = "other"
                    if parent_data["child_parent_ids"]:
                        child_data = self.odoo.read(
                            "account.account",
                            parent_data["child_parent_ids"][0],
                            ["type"],
                        )
                        acc_type = child_data["type"]
                    account_id = self.odoo.create(
                        "account.account",
                        {
                            "code": odoo_code,
                            "name": acc_data["name"],
                            "type": acc_type,
                            "user_type": parent_data["user_type"][0],
                            "parent_id": parent_ids[0],
                        },
                    )
                    self.d[getKey(aa, acc_data["id"])] = account_id
        return True

    def migrate_party_party(self):
        if self.esale:
            self.crT.execute(
                "select id,code,active,name,comment,trade_name,"
                "write_date,create_date,"
                "esale_email,attributes,manual_code,include_347,"
                "(select code from party_identifier "
                "where party = party_party.id) as vat,"
                "(select min(value) from party_contact_mechanism where"
                " party = party_party.id and address is null and "
                "type = 'email' and active=true) as email,(select "
                "min(value) from party_contact_mechanism where party ="
                "party_party.id and address is null and type = 'phone'"
                " and active=true) as phone,(select min(value) from "
                "party_contact_mechanism where party = party_party.id "
                "and address is null and type = 'fax' and active=true)"
                " as fax,(select min(value) from "
                "party_contact_mechanism where party = party_party.id "
                "and address is null and type = 'website' and "
                "active=true) as website from party_party "
                "where id != 1"
            )
        else:
            self.crT.execute(
                "select id,code,active,name,comment,trade_name,"
                "write_date,create_date,include_347,"
                "(select code from party_identifier "
                "where party = party_party.id) as vat,"
                "(select min(value) from party_contact_mechanism where"
                " party = party_party.id and address is null and "
                "type = 'email' and active=true) as email,(select "
                "min(value) from party_contact_mechanism where party ="
                "party_party.id and address is null and type = 'phone'"
                " and active=true) as phone,(select min(value) from "
                "party_contact_mechanism where party = party_party.id "
                "and address is null and type = 'fax' and active=true)"
                " as fax,(select min(value) from "
                "party_contact_mechanism where party = party_party.id "
                "and address is null and type = 'website' and "
                "active=true) as website from party_party "
                "where id != 1"
            )
        data = self.crT.fetchall()
        pp = "party_party"
        pa = "party_address"
        self.d[getKey(pp, 1)] = 1  # res_company
        self.d[getKey(pa, 1)] = 1  # res_company

        for part_data in data:
            no_update = False
            if self.d.has_key(getKey(pp, part_data["id"])):
                partner_id = self.d[getKey(pp, part_data["id"])]
                tr_date = part_data["write_date"] or part_data["create_date"]
                if tr_date <= self.last_update:
                    no_update = True
            if not no_update:
                vals = {
                    "ref": part_data["code"] or False,
                    "active": part_data["active"],
                    "name": part_data["name"],
                    "comercial": part_data["trade_name"] or False,
                    "email": part_data["email"] or False,
                    "not_in_mod347": not part_data["include_347"] and True or False,
                    "phone": part_data["phone"] or False,
                    "fax": part_data["fax"] or False,
                    "website": part_data["website"] or False,
                    "comment": part_data["comment"] or False,
                    "is_company": True,
                }
                if part_data.get("esale_email"):
                    vals["email"] = part_data["esale_email"]

                if part_data.get("attributes"):
                    attributes = eval(part_data["attributes"])
                    if attributes.get("medical_code", False):
                        vals["medical_code"] = attributes["medical_code"]
                    if attributes.get("timetable", False):
                        vals["timetable"] = attributes["timetable"]
                if part_data.get("manual_code"):
                    if (
                        vals.get("medical_code", False)
                        and vals["medical_code"] != part_data["manual_code"]
                    ):
                        print (
                            "diferencia en codigo medico del partner %s"
                            % part_data["id"]
                        )
                    vals["medical_code"] = part_data["manual_code"]

                self.crT.execute(
                    "select count(*) from sale_sale where party "
                    "= %s" % (part_data["id"])
                )
                result = self.crT.fetchone()
                if result and result["count"]:
                    vals["customer"] = True

                self.crT.execute(
                    "select count(*) from purchase_purchase where"
                    " party = %s" % (part_data["id"])
                )
                result = self.crT.fetchone()
                if result and result["count"]:
                    vals["supplier"] = True

                print "vals: ", vals
                if self.d.has_key(getKey(pp, part_data["id"])):
                    partner_id = self.d[getKey(pp, part_data["id"])]
                    self.odoo.write("res.partner", partner_id, vals)
                else:
                    partner_id = self.odoo.create("res.partner", vals)
                if part_data.get("vat", False):
                    try:
                        self.odoo.write(
                            "res.partner", [partner_id], {"vat": part_data["vat"]}
                        )
                    except:
                        print "VAT not valid: ", part_data["vat"]
                self.d[getKey(pp, part_data["id"])] = partner_id
            self.crT.execute(
                "select party_address.id,city,party_address.name,zip,"
                "streetbis,street,active,party,comment_shipment,"
                "party_address.write_date,party_address.create_date,"
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
                "where party = %s order by invoice desc" % (part_data["id"])
            )
            add_data = self.crT.fetchall()
            partner_address = False
            for add in add_data:
                if self.d.has_key(getKey(pa, add["id"])):
                    add_date = add["write_date"] or add["create_date"]
                    if add_date <= self.last_update:
                        partner_address = True
                        continue
                vals = {
                    "street": add["street"] or False,
                    "street2": add["streetbis"] or False,
                    "zip": add["zip"] or False,
                    "city": add["city"] or False,
                }
                if add["code"]:
                    country_ids = self.odoo.search(
                        "res.country", [("code", "=", add["code"])]
                    )
                    if country_ids:
                        vals["country_id"] = country_ids[0]
                        if add["code"] == "ES" and add["zip"]:
                            state_ids = self.odoo.search(
                                "res.country.state",
                                [
                                    ("country_id", "=", country_ids[0]),
                                    ("code", "=", add["zip"][:2]),
                                ],
                            )
                            if state_ids:
                                vals["state_id"] = state_ids[0]

                if not partner_address:
                    self.odoo.write("res.partner", [partner_id], vals)
                    partner_address = True
                    self.d[getKey(pa, add["id"])] = partner_id
                else:
                    vals.update(
                        {
                            "parent_id": partner_id,
                            "name": add["name"] or "/",
                            "active": add["active"],
                            "carrier_notes": add["comment_shipment"] or False,
                            "phone": part_data["phone"] or False,
                            "fax": part_data["fax"] or False,
                            "website": part_data["website"] or False,
                            "email": part_data["email"] or False,
                            "use_parent_address": False,
                        }
                    )
                    if add["delivery"]:
                        vals["type"] = "delivery"
                    print "vals: ", vals
                    if self.d.has_key(getKey(pa, add["id"])):
                        add_id = self.d[getKey(pa, add["id"])]
                        if add_id == partner_id:
                            del vals["parent_id"]
                        self.odoo.write("res.partner", [add_id], vals)
                    else:
                        add_id = self.odoo.create("res.partner", vals)
                        self.d[getKey(pa, add["id"])] = add_id

        return True

    def migrate_party_category(self):
        self.crO.execute("delete from res_partner_category")
        self.close_crO()
        self.crT.execute(
            "select id,name, parent,active from party_category " "order by parent desc"
        )
        data = self.crT.fetchall()
        pc = "party_category"
        pp = "party_party"
        for cat_data in data:
            vals = {"name": cat_data["name"], "active": cat_data["active"]}
            if cat_data.get("parent", False):
                vals["parent_id"] = self.d[getKey(pc, cat_data["parent"])]
            print "vals: ", vals
            cat_id = self.odoo.create("res.partner.category", vals)
            self.d[getKey(pc, cat_data["id"])] = cat_id

        self.crT.execute("select category,party from party_category_rel")
        partner_data = self.crT.fetchall()
        for part_data in partner_data:
            partner_id = self.d[getKey(pp, part_data["party"])]
            category_id = self.d[getKey(pc, part_data["category"])]
            partner_data = self.odoo.read("res.partner", partner_id, ["category_id"])
            if category_id not in partner_data["category_id"]:
                self.odoo.write(
                    "res.partner", [partner_id], {"category_id": [(4, category_id)]}
                )
        return True

    def migrate_account_journal(self):
        BY_DEFAULT_JOURNALS = {
            "sale": ["VEN"],
            "cash": ["BAN1"],
            "bank": ["BAN2"],
            "purchase": ["COMPR"],
            #'general': ['Vario'],
            "general": [],
            "situation": [],
            "sale_refund": ["AVENT"],
        }
        JOURNAL_TYPE_MAP = {
            "revenue": ["sale", "sale_refund"],
            "expense": ["purchase"],
            "cash": ["bank"],
            "commission": ["general"],
            "general": ["general"],
            "situation": ["situation"],
            "write-off": ["general"],
        }
        self.crT.execute(
            "select id,update_posted,code,type,name " "from account_journal"
        )
        data = self.crT.fetchall()
        aj = "account_journal"
        ajr = "account_journal_refund"
        tt = "account_fiscalyear"
        first_journal_id = self.odoo.search("account.journal", [])[0]
        first_journal_data = self.odoo.read(
            "account.journal", first_journal_id, ["sequence_id"]
        )
        journal_seq_id = first_journal_data["sequence_id"][0]

        for journal_data in data:
            journal_id = False
            vals = {
                "name": journal_data["name"],
                "update_posted": journal_data["update_posted"],
                "sequence_id": journal_seq_id,
                "code": journal_data["code"],
            }
            if journal_data["name"] == "Cash":
                vals["type"] = "cash"
            elif len(JOURNAL_TYPE_MAP[journal_data["type"]]) == 1:
                vals["type"] = JOURNAL_TYPE_MAP[journal_data["type"]][0]

            if vals.get("type", False):
                if BY_DEFAULT_JOURNALS[vals["type"]]:
                    journal_code = BY_DEFAULT_JOURNALS[vals["type"]].pop()
                    journal_id = self.odoo.search(
                        "account.journal", [("code", "=", journal_code)]
                    )[0]
                if journal_id:
                    print "write vals: ", vals
                    self.odoo.write("account.journal", [journal_id], vals)
                    self.d[getKey(aj, journal_data["id"])] = journal_id
                else:
                    print "create vals: ", vals
                    journal_id = self.odoo.create("account.journal", vals)
                    self.d[getKey(aj, journal_data["id"])] = journal_id
            else:
                if self.esale:
                    self.crT.execute(
                        "select fiscalyear,out_iss.name "
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
                        "order by fiscalyear asc" % (journal_data["id"])
                    )
                    seq_data = self.crT.fetchall()
                else:
                    seq_data = []
                out_invoice_seq = False
                out_refund_seq = False
                for jtype in JOURNAL_TYPE_MAP[journal_data["type"]]:
                    vals["type"] = jtype
                    journal_id = False
                    if jtype == "sale":
                        m = aj
                        if out_invoice_seq:
                            vals["invoice_sequence_id"] = out_invoice_seq
                        else:
                            for seq in seq_data:
                                svals = {
                                    "name": seq["out_name"],
                                    "implementation": "no_gap",
                                    "prefix": seq["out_prefix"],
                                    "padding": seq["out_padding"],
                                    "number_next_actual": seq["out_number_next"],
                                    "number_increment": seq["out_increment"],
                                }

                                seq_id = self.odoo.create("ir.sequence", svals)
                                if not out_invoice_seq:
                                    out_invoice_seq = seq_id
                                    vals["invoice_sequence_id"] = out_invoice_seq
                                else:
                                    year_seq = self.odoo.create("ir.sequence", svals)
                                    self.odoo.create(
                                        "account.sequence.fiscalyear",
                                        {
                                            "sequence_id": year_seq,
                                            "fiscalyear_id": self.d[
                                                getKey(tt, seq["fiscalyear"])
                                            ],
                                            "sequence_main_id": out_invoice_seq,
                                        },
                                    )
                    elif jtype == "sale_refund":
                        m = ajr
                        vals["code"] = u"A" + vals["code"]
                        vals["name"] = u"Ab. " + vals["name"]
                        if out_refund_seq:
                            vals["invoice_sequence_id"] = out_refund_seq
                        else:
                            for seq in seq_data:
                                svals = {
                                    "name": seq["ref_name"],
                                    "implementation": "no_gap",
                                    "prefix": seq["ref_prefix"],
                                    "padding": seq["ref_padding"],
                                    "number_next_actual": seq["ref_number_next"],
                                    "number_increment": seq["ref_increment"],
                                }

                                seq_id = self.odoo.create("ir.sequence", svals)
                                if not out_refund_seq:
                                    out_refund_seq = seq_id
                                    vals["invoice_sequence_id"] = out_refund_seq
                                else:
                                    year_seq = self.odoo.create("ir.sequence", svals)
                                    self.odoo.create(
                                        "account.sequence.fiscalyear",
                                        {
                                            "sequence_id": year_seq,
                                            "fiscalyear_id": self.d[
                                                getKey(tt, seq["fiscalyear"])
                                            ],
                                            "sequence_main_id": out_refund_seq,
                                        },
                                    )
                    if BY_DEFAULT_JOURNALS[vals["type"]]:
                        journal_code = BY_DEFAULT_JOURNALS[vals["type"]].pop()
                        journal_id = self.odoo.search(
                            "account.journal", [("code", "=", journal_code)]
                        )[0]
                    if journal_id:
                        print "write vals: ", vals
                        self.odoo.write("account.journal", [journal_id], vals)
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
            bank_ids = self.odoo.search(
                "res.bank", [("code", "=", bnk_data["bank_code"])]
            )
            if bank_ids:
                self.d[getKey(bnk, bnk_data["id"])] = bank_ids[0]
            else:
                partner_id = self.d[getKey(pp, bnk_data["party"])]
                if partner_id:
                    partner_data = self.odoo.read(
                        "res.partner",
                        partner_id,
                        [
                            "name",
                            "street",
                            "street2",
                            "zip",
                            "city",
                            "state_id",
                            "country_id",
                            "phone",
                            "fax",
                            "email",
                            "website",
                            "vat",
                        ],
                    )
                    vals = {
                        "name": partner_data["name"],
                        "street": partner_data["street"],
                        "street2": partner_data["street2"],
                        "zip": partner_data["zip"],
                        "city": partner_data["city"],
                        "state": partner_data["state_id"]
                        and partner_data["state_id"][0]
                        or False,
                        "country": partner_data["country_id"]
                        and partner_data["country_id"][0]
                        or False,
                        "phone": partner_data["phone"],
                        "fax": partner_data["fax"],
                        "email": partner_data["email"],
                        "vat": partner_data["vat"],
                        "code": bnk_data["bank_code"],
                        "bic": (bnk_data["bic"] and bnk_data["bic"] != "")
                        and bnk_data["bic"]
                        or False,
                    }
                    bank_id = self.odoo.create("res.bank", vals)
                    self.d[getKey(bnk, bnk_data["id"])] = bank_id

        return True

    def migrate_bank_accounts(self):
        self.crT.execute(
            "select bank_account.id,bank,active,owner,type,"
            'number from "bank_account-party_party" bapp '
            "inner join bank_account on bapp.account = "
            "bank_account.id inner join bank_account_number on "
            "bank_account_number.account = bank_account.id"
        )
        data = self.crT.fetchall()
        pp = "party_party"
        bnk = "bank"
        ba = "bank_account"
        for acc_data in data:
            bank_id = self.d[getKey(bnk, acc_data["bank"])]
            bank_data = self.odoo.read("res.bank", bank_id, ["country", "name", "bic"])
            owner_id = self.d[getKey(pp, acc_data["owner"])]
            owner_data = self.odoo.read(
                "res.partner",
                owner_id,
                ["name", "street", "zip", "city", "state_id", "country_id"],
            )
            vals = {
                "state": acc_data["type"] == "other" and "bank" or acc_data["type"],
                "acc_number": acc_data["number"],
                "acc_country_id": bank_data["country"]
                and bank_data["country"][0]
                or False,
                "bank": bank_id,
                "bank_name": bank_data["name"],
                "bank_bic": bank_data["bic"] or False,
                "active": acc_data["active"],
                "partner_id": owner_id,
                "owner_name": owner_data["name"],
                "street": owner_data["street"],
                "zip": owner_data["zip"],
                "city": owner_data["city"],
                "state_id": owner_data["state_id"]
                and owner_data["state_id"][0]
                or False,
                "country_id": owner_data["country_id"]
                and owner_data["country_id"][0]
                or False,
            }
            print "VALS: ", vals
            if self.d.has_key(getKey(ba, acc_data["id"])) and self.odoo.read(
                "res.partner.bank", self.d[getKey(ba, acc_data["id"])], []
            ):
                print "WRITE"
                self.odoo.write(
                    "res.partner.bank", self.d[getKey(ba, acc_data["id"])], vals
                )
            else:
                print "CREATE"
                acc_id = self.odoo.create("res.partner.bank", vals)
                self.d[getKey(ba, acc_data["id"])] = acc_id

        return True

    def unlink_move(self, move_key):
        move_id = self.d[move_key]
        move_data = self.odoo.read("account.move", move_id, [])
        if move_data:
            invoices = self.odoo.search("account.invoice", [("move_id", "=", move_id)])
            self.odoo.write("account.invoice", invoices, {"move_id": False})
            move_lines = self.odoo.search(
                "account.move.line", [("move_id", "=", move_id)]
            )
            move_line_data = self.odoo.read(
                "account.move.line", move_lines, ["reconcile_id"]
            )
            for move_line in move_line_data:
                if move_line["reconcile_id"]:
                    self.odoo.unlink(
                        "account.move.reconcile", move_line["reconcile_id"][0]
                    )
            self.odoo.execute("account.move", "button_cancel", [move_id])
            self.odoo.unlink("account.move.line", move_lines)
            self.odoo.unlink("account.move", move_id)
            self.d.pop(move_key)

    def migrate_account_moves(self):
        self.crT.execute(
            "select id,post_number,journal,period,date,state,"
            "create_date,write_date,description from "
            "account_move"
        )
        data = self.crT.fetchall()
        am = "account_move"
        aml = "account_move_line"
        aj = "account_journal"
        ap = "account_period"
        pp = "party_party"
        aa = "account_account"
        tr_move_ids = ["account_move_%s" % x["id"] for x in data]
        print "LEN: ", len(tr_move_ids)
        move_keys = [
            x
            for x in self.d.keys()
            if "account_move" in x
            and "account_move_line" not in x
            and "account_move_reconciliation" not in x
            and x not in tr_move_ids
        ]
        print "Filter LEN: ", len(move_keys)
        for move_key in move_keys:
            self.unlink_move(move_key)
        for move_data in data:
            if self.d.has_key(getKey(am, move_data["id"])):
                tr_date = move_data["write_date"] or move_data["create_date"]
                self.crT.execute(
                    "select create_date,write_date from "
                    "account_move_line where move=%s" % move_data["id"]
                )
                line_dates = self.crT.fetchall()
                for line in line_dates:
                    l_tr_date = line["write_date"] or line["create_date"]
                    if l_tr_date > tr_date:
                        tr_date = l_tr_date
                print "tr_date: ", tr_date
                if tr_date <= self.last_update:
                    continue
                elif self.odoo.read(
                    "account.move", self.d[getKey(am, move_data["id"])], ["name"]
                ):
                    print "DEL ID: ", self.d[getKey(am, move_data["id"])]
                    self.unlink_move(getKey(am, move_data["id"]))

            period_id = self.d[getKey(ap, move_data["period"])]
            journal_id = self.d[getKey(aj, move_data["journal"])]
            vals = {
                "journal_id": journal_id,
                "period_id": period_id,
                "ref": move_data["description"] or "",
                "date": format_date(move_data["date"]),
                "name": move_data["post_number"] or "/",
            }
            print "vals: ", vals
            move_id = self.odoo.create("account.move", vals)
            self.d[getKey(am, move_data["id"])] = move_id
            self.crT.execute(
                "select aml.id,debit,description,account,credit,"
                "party,maturity_date,payment_type,"
                "atl.code as tax_code,atl.amount as tax_amount "
                "from account_move_line aml left join "
                "account_tax_line atl on atl.move_line = "
                "aml.id where move = %s" % (move_data["id"])
            )
            line_data = self.crT.fetchall()
            for line in line_data:
                partner_id = False
                if line["party"]:
                    partner_id = self.d[getKey(pp, line["party"])]
                account_id = self.d[getKey(aa, line["account"])]
                tax_code_id = False
                if line["tax_code"]:
                    tax_code_id = self.TAX_CODES_MAP[str(line["tax_code"])]

                lines_vals = {
                    "name": line["description"] or "-",
                    "journal_id": journal_id,
                    "period_id": period_id,
                    "partner_id": partner_id,
                    "account_id": account_id,
                    "debit": float(line["debit"]),
                    "credit": float(line["credit"]),
                    "date": format_date(move_data["date"]),
                    "date_maturity": line["maturity_date"]
                    and format_date(line["maturity_date"])
                    or False,
                    "move_id": move_id,
                    "tax_code_id": tax_code_id,
                    "tax_amount": line["tax_amount"]
                    and float(line["tax_amount"])
                    or 0.0,
                }
                if lines_vals["debit"] and lines_vals["debit"] < 0:
                    lines_vals["credit"] = abs(lines_vals["debit"])
                    lines_vals["debit"] = 0.0
                elif lines_vals["credit"] and lines_vals["credit"] < 0:
                    lines_vals["debit"] = abs(lines_vals["credit"])
                    lines_vals["credit"] = 0.0
                update = True
                if self.d.has_key(getKey(aml, line["id"])):
                    line_ids = self.odoo.search(
                        "account.move.line",
                        [("id", "=", self.d[getKey(aml, line["id"])])],
                    )
                    if line_ids:
                        lines_vals["debit"] = 0.0
                        lines_vals["credit"] = 0.0
                        update = False
                print "lines_vals: ", lines_vals
                move_line_id = self.odoo.create("account.move.line", lines_vals)
                if update:
                    self.d[getKey(aml, line["id"])] = move_line_id

            if move_data["state"] == "posted":
                self.odoo.execute("account.move", "post", [move_id])
                print "POST"
        return True

    def migrate_account_reconciliation(self):
        self.crT.execute("select id,name from account_move_reconciliation")
        data = self.crT.fetchall()
        amr = "account_move_reconciliation"
        aml = "account_move_line"
        for rec in data:
            print "rec"
            vals = {"name": rec["name"], "type": "auto"}
            create = True
            if self.d.has_key(getKey(amr, rec["id"])):
                reconcile_ids = self.odoo.search(
                    "account.move.reconcile",
                    [("id", "=", self.d[getKey(amr, rec["id"])])],
                )
                if reconcile_ids:
                    create = False
                    rec_id = self.d[getKey(amr, rec["id"])]
            if create:
                rec_id = self.odoo.create("account.move.reconcile", vals)
                self.d[getKey(amr, rec["id"])] = rec_id

            self.crT.execute(
                "select id from account_move_line where "
                "reconciliation = %s" % (rec["id"])
            )
            lines_data = self.crT.fetchall()
            for line in lines_data:
                print "line: ", line["id"]
                move_line_id = self.d[getKey(aml, line["id"])]
                line_data = self.odoo.read("account.move.line", move_line_id, [])
                if line_data:
                    self.odoo.write(
                        "account.move.line", [move_line_id], {"reconcile_id": rec_id}
                    )
        print "finish rec"
        return True

    def migrate_product_category(self):
        self.crT.execute(
            "select id,name,parent from product_category order "
            "by parent asc nulls first"
        )
        data = self.crT.fetchall()
        pc = "product_category"
        for cat in data:
            if self.d.has_key(getKey(pc, cat["id"])):
                continue
            parent_id = False
            if cat["parent"]:
                parent_id = self.d[getKey(pc, cat["parent"])]
            vals = {"name": cat["name"], "parent_id": parent_id, "type": "normal"}
            cat_id = self.odoo.create("product.category", vals)
            self.d[getKey(pc, cat["id"])] = cat_id
        print "finish categ"
        return True

    def migrate_product_uom(self):
        UOM_CAT_MAP = {
            "1": 1,  # Unidades
            "2": 2,  # Peso
            "3": 3,  # Horario
            "4": 4,  # Longitud
            "5": 5,  # Volumen
            "6": 6,
        }  # Superficie (Hay que crearla)
        self.crT.execute(
            "select id,name,category,rounding,rate,active from " "product_uom"
        )
        data = self.crT.fetchall()
        pu = "product_uom"
        for uom_data in data:
            if str(uom_data["id"]) in self.UOM_MAP:
                self.d[getKey(pu, uom_data["id"])] = self.UOM_MAP[str(uom_data["id"])]
            else:
                vals = {
                    "name": uom_data["name"],
                    "category_id": UOM_CAT_MAP[str(uom_data["category"])],
                    "rounding": float(uom_data["rounding"]),
                    "factor": float(uom_data["rate"]),
                    "active": uom_data["active"],
                    "uom_type": uom_data["rate"] > 1
                    and "smaller"
                    or (
                        uom_data["rate"] == 1
                        and "reference"
                        or uom_data["rate"] < 1
                        and "bigger"
                        or "reference"
                    ),
                }
                if self.d.has_key(getKey(pu, uom_data["id"])):
                    self.odoo.write(
                        "product.uom", self.d[getKey(pu, uom_data["id"])], vals
                    )
                else:
                    uom_id = self.odoo.create("product.uom", vals)
                    self.d[getKey(pu, uom_data["id"])] = uom_id
        print "finish uom"
        return True

    def migrate_product_product(self):
        if self.esale:
            self.crT.execute(
                "select pp.id,category,name,default_uom,pp.active,"
                "pp.create_date,pp.write_date,pt.create_date as "
                "tcreate_date,pt.write_date as twrite_date,"
                "consumable,type,purchasable,purchase_uom,salable,"
                "sale_uom,delivery_time,base_code,weight_uom,"
                "kit_fixed_list_price,kit,pt.id as template_id,"
                "stock_depends_on_kit_components,number,taxes_category"
                " from product_product pp inner join product_template "
                "pt on pt.id = pp.template left join product_code pc "
                "on pc.product = pp.id and barcode='EAN' and "
                "pc.active = true"
            )
        else:
            self.crT.execute(
                "select pp.id,category,name,default_uom,pp.active,"
                "pp.create_date,pp.write_date,pt.create_date as "
                "tcreate_date,pt.write_date as twrite_date,"
                "consumable,type,purchasable,purchase_uom,salable,"
                "sale_uom,delivery_time,code,"
                "kit_fixed_list_price,kit,pt.id as template_id,"
                "stock_depends_on_kit_components,number,taxes_category"
                " from product_product pp inner join product_template "
                "pt on pt.id = pp.template left join product_code pc "
                "on pc.product = pp.id and barcode='EAN' and "
                "pc.active = true"
            )
        data = self.crT.fetchall()
        pc = "product_category"
        pp = "product_product"
        pu = "product_uom"
        aa = "account_account"
        account_expense_field = False
        account_incoming_field = False
        cost_method_field = False
        list_price_field = False
        cost_price_field = False
        for prod in data:
            if self.d.has_key(getKey(pp, prod["id"])):
                pp_date = prod["write_date"] or prod["create_date"]
                pt_date = prod["twrite_date"] or prod["tcreate_date"]
                tr_date = max([pp_date, pt_date])
                if tr_date <= self.last_update:
                    continue
            categ_id = self.d[getKey(pc, prod["category"])]
            if prod["default_uom"]:
                default_uom_id = self.d[getKey(pu, prod["default_uom"])]
            else:
                default_uom_id = 1
            if prod["purchase_uom"]:
                purchase_uom_id = self.d[getKey(pu, prod["purchase_uom"])]
            else:
                purchase_uom_id = 1
            vals = {
                "name": prod["name"],
                "uom_id": default_uom_id,
                "active": prod["active"],
                "type": prod["type"] != "goods"
                and prod["type"]
                or (prod["consumable"] and "consu" or "product"),
                "purchase_ok": prod["purchasable"] or False,
                "uom_po_id": purchase_uom_id,
                "sale_ok": prod["salable"] or False,
                "pack_fixed_price": prod["kit_fixed_list_price"] or False,
                "sale_delay": prod["delivery_time"]
                and float(prod["delivery_time"])
                or 0,
                "default_code": "",
                "stock_depends": prod["stock_depends_on_kit_components"] or False,
                "categ_id": categ_id,
            }
            if prod.get("base_code"):
                vals["default_code"] = prod["base_code"]
            elif prod.get("code"):
                vals["default_code"] = prod["code"]

            if prod.get("weight_uom"):
                vals["weight"] = prod["weight_uom"] and float(prod["weight_uom"]) or 0.0
            if prod["taxes_category"]:
                self.crT.execute(
                    "select tax from "
                    "product_category_customer_taxes_rel "
                    "where category = %s" % (prod["category"])
                )
                tax_data = self.crT.fetchall()
                taxes_ids = []
                for tax in tax_data:
                    tax_id = self.TAXES_MAP[str(tax["tax"])]
                    taxes_ids.extend(tax_id)
                if taxes_ids:
                    vals["taxes_id"] = [(6, 0, taxes_ids)]
                self.crT.execute(
                    "select tax from "
                    "product_category_supplier_taxes_rel "
                    "where category = %s" % (prod["category"])
                )
                tax_data = self.crT.fetchall()
                taxes_ids = []
                for tax in tax_data:
                    tax_id = self.TAXES_MAP[str(tax["tax"])]
                    taxes_ids.extend(tax_id)
                if taxes_ids:
                    vals["supplier_taxes_id"] = [(6, 0, taxes_ids)]
            else:
                self.crT.execute(
                    "select tax from "
                    "product_customer_taxes_rel "
                    "where product = %s" % (prod["template_id"])
                )
                tax_data = self.crT.fetchall()
                taxes_ids = []
                for tax in tax_data:
                    tax_id = self.TAXES_MAP[str(tax["tax"])]
                    taxes_ids.extend(tax_id)
                if taxes_ids:
                    vals["taxes_id"] = [(6, 0, taxes_ids)]
                self.crT.execute(
                    "select tax from "
                    "product_supplier_taxes_rel "
                    "where product = %s" % (prod["template_id"])
                )
                tax_data = self.crT.fetchall()
                taxes_ids = []
                for tax in tax_data:
                    tax_id = self.TAXES_MAP[str(tax["tax"])]
                    taxes_ids.extend(tax_id)
                if taxes_ids:
                    vals["supplier_taxes_id"] = [(6, 0, taxes_ids)]

            # Propiedades
            # Cost method
            if not cost_method_field:
                self.crT.execute(
                    "select id from ir_model_field where name = "
                    "'cost_price_method' and module = 'product'"
                )
                field = self.crT.fetchone()
                cost_method_field = field["id"]
            self.crT.execute(
                "select value from ir_property where field = %s "
                "and res = 'product.template,%s' limit 1"
                % (cost_method_field, prod["template_id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                field_value = field_value["value"].replace(",", "")
                vals["cost_method"] = (
                    field_value == "fixed" and "standard" or field_value
                )
            # list_price
            if not list_price_field:
                self.crT.execute(
                    "select id from ir_model_field where name = "
                    "'list_price' and module = 'product'"
                )
                field = self.crT.fetchone()
                list_price_field = field["id"]
            self.crT.execute(
                "select value from ir_property where field = %s "
                "and res = 'product.template,%s' limit 1"
                % (list_price_field, prod["template_id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                field_value = field_value["value"].replace(",", "")
                vals["list_price"] = float(field_value)
            # cost_price
            if not cost_price_field:
                self.crT.execute(
                    "select id from ir_model_field where name = "
                    "'cost_price' and module = 'product'"
                )
                field = self.crT.fetchone()
                cost_price_field = field["id"]
            self.crT.execute(
                "select value from ir_property where field = %s "
                "and res = 'product.template,%s' limit 1"
                % (cost_price_field, prod["template_id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                field_value = field_value["value"].replace(",", "")
                vals["standard_price"] = float(field_value)
            # account_expense
            if not account_expense_field:
                self.crT.execute(
                    "select id from ir_model_field where name = "
                    "'account_expense' and module = "
                    "'account_product'"
                )
                field = self.crT.fetchone()
                account_expense_field = field["id"]
            self.crT.execute(
                "select value from ir_property where field = %s "
                "and res = 'product.template,%s' limit 1"
                % (account_expense_field, prod["template_id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                field_value = field_value["value"].split(",")[1]
                account_id = self.d[getKey(aa, int(field_value))]
                vals["property_account_expense"] = account_id
            # account_revenue
            if not account_incoming_field:
                self.crT.execute(
                    "select id from ir_model_field where name = "
                    "'account_revenue' and module = "
                    "'account_product'"
                )
                field = self.crT.fetchone()
                account_incoming_field = field["id"]
            self.crT.execute(
                "select value from ir_property where field = %s "
                "and res = 'product.template,%s' limit 1"
                % (account_incoming_field, prod["template_id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                field_value = field_value["value"].split(",")[1]
                account_id = self.d[getKey(aa, int(field_value))]
                vals["property_account_income"] = account_id

            print "vals: ", vals
            if self.d.has_key(getKey(pp, prod["id"])):
                prod_id = self.d[getKey(pp, prod["id"])]
                self.odoo.write("product.product", [prod_id], vals)
                kit_lines = self.odoo.search(
                    "product.pack.line", [("parent_product_id", "=", prod_id)]
                )
                if kit_lines:
                    self.odoo.unlink("product.pack.line", kit_lines)
                    self.migrate_kits(prod["id"])
            else:
                prod_id = self.odoo.create("product.product", vals)
                # self.migrate_kits(prod["id"])
            if prod.get("number", False):
                try:
                    self.odoo.write(
                        "product.product", [prod_id], {"ean13": prod["number"]}
                    )
                except:
                    try:
                        self.odoo.write(
                            "product.product", [prod_id], {"ean14": prod["number"]}
                        )
                    except:
                        pass
            self.d[getKey(pp, prod["id"])] = prod_id
        return True

    def migrate_kits(self, parent):
        self.crT.execute(
            "select product,quantity from " "product_kit_line where parent=%s" % parent
        )
        kit_data = self.crT.fetchall()
        pp = "product_product"
        for kit_line in kit_data:
            lin_prod_id = self.d[getKey(pp, kit_line["product"])]
            kit_prod_id = self.d[getKey(pp, parent)]
            vals = {
                "quantity": float(kit_line["quantity"]),
                "product_id": lin_prod_id,
                "parent_product_id": kit_prod_id,
            }
            print "vals: ", vals
            self.odoo.create("product.pack.line", vals)
        return True

    def _get_magento_id(self, model_name, tryton_id):
        self.crT.execute("select id from ir_model where model = " "'%s'" % model_name)
        ir_model_id = self.crT.fetchall()
        self.crT.execute(
            "select mgn_id from magento_external_referential "
            "where try_id=%s and model=%s" % (tryton_id, ir_model_id[0][0])
        )
        return self.crT.fetchall()[0][0]

    def migrate_magento_metadata(self):
        self.crT.execute("select id,name,username,uri,password from " "magento_app")
        backend_data = self.crT.fetchall()
        ma = "magento_app"
        msv = "magento_storeview"
        mw = "magento_website"
        msg = "magento_storegroup"
        for backend_line in backend_data:
            vals = {
                "version": "1.7",
                "name": backend_line["name"],
                "location": backend_line["uri"],
                "username": backend_line["username"],
                "password": backend_line["password"],
                "warehouse_id": self.odoo.search("stock.warehouse", [], limit=1)[0],
            }
            backend_id = self.odoo.create("magento.backend", vals)
            self.d[getKey(ma, backend_line["id"])] = backend_id

        self.crT.execute("select id,magento_app,code,name from " "magento_website")
        website_data = self.crT.fetchall()
        for website_line in website_data:
            mag_id = self._get_magento_id("magento.website", website_line["id"])
            vals = {
                "code": website_line["code"],
                "name": website_line["name"],
                "backend_id": self.d[getKey(ma, website_line["magento_app"])],
                "magento_id": mag_id,
            }
            website_id = self.odoo.create("magento.website", vals)
            self.d[getKey(mw, website_line["id"])] = website_id

        self.crT.execute("select id,magento_website,name from " "magento_storegroup")
        storegroup_data = self.crT.fetchall()
        for storegroup_line in storegroup_data:
            mag_id = self._get_magento_id("magento.storegroup", storegroup_line["id"])
            vals = {
                "website_id": self.d[getKey(mw, storegroup_line["magento_website"])],
                "name": storegroup_line["name"],
                "magento_id": mag_id,
            }
            store_id = self.odoo.create("magento.store", vals)
            self.d[getKey(msg, storegroup_line["id"])] = store_id

        self.crT.execute(
            "select id,code,name,magento_storegroup from " "magento_storeview"
        )
        storeview_data = self.crT.fetchall()
        for storeview_line in storeview_data:
            mag_id = self._get_magento_id("magento.storeview", storeview_line["id"])
            vals = {
                "store_id": self.d[getKey(msg, storeview_line["magento_storegroup"])],
                "name": storeview_line["name"],
                "code": storeview_line["code"],
                "magento_id": mag_id,
            }
            store_id = self.odoo.create("magento.storeview", vals)
            self.d[getKey(msv, storeview_line["id"])] = store_id
        return True

    def migrate_magento_payment_mode(self):
        self.crT.execute("SELECT id,code,payment_type FROM esale_payment")
        epayment_data = self.crT.fetchall()
        for epayment_line in epayment_data:
            if self.d.has_key(getKey("esale_payment", epayment_line["id"])):
                continue
            vals = {
                "name": epayment_line["code"],
                "payment_mode_id": self.PAYMENT_MODES_MAP[
                    str(epayment_line["payment_type"])
                ],
            }
            method_id = self.odoo.create("payment.method", vals)
            self.d[getKey("esale_payment", epayment_line["id"])] = method_id

    def delete_invoice(self, key):
        self.crO.execute(
            "delete from account_invoice_line where invoice_id " "= %s" % self.d[key]
        )
        self.crO.execute(
            "delete from account_invoice_tax where " "invoice_id = %s" % self.d[key]
        )
        self.crO.execute("delete from account_invoice where id = %s" % self.d[key])
        self.close_crO()

    def migrate_invoices(self):
        self.crT.execute(
            "select comment,reference,payment_term,move,number,"
            "description,state,party,type,journal,account,"
            "create_date,write_date,"
            "invoice_date,invoice_address,payment_type,id,"
            "bank_account from account_invoice"
        )
        data = self.crT.fetchall()
        ai = "account_invoice"
        aa = "account_account"
        am = "account_move"
        pa = "party_address"
        aj = "account_journal"
        ba = "bank_account"
        pt = "product_product"
        ail = "account_invoice_line"
        pu = "product_uom"
        INV_TYPE_MAP = {
            "in_invoice": "in_invoice",
            "out_credit_note": "out_refund",
            "in_credit_note": "in_refund",
            "out_invoice": "out_invoice",
        }

        tr_move_ids = ["account_invoice_%s" % x["id"] for x in data]
        move_keys = [
            x
            for x in self.d.keys()
            if "account_invoice" in x
            and "account_invoice_line" not in x
            and x not in tr_move_ids
        ]
        for move_key in move_keys:
            self.delete_invoice(move_key)
            self.d.pop(move_key)
        for invoice in data:
            if self.d.has_key(getKey(ai, invoice["id"])):
                tr_date = invoice["write_date"] or invoice["create_date"]
                if tr_date <= self.last_update:
                    continue
                else:
                    self.delete_invoice(getKey(ai, invoice["id"]))
            journal_id = self.d[getKey(aj, invoice["journal"])]
            bank_account_id = False
            if invoice["bank_account"] and self.d.has_key(
                getKey(ba, invoice["bank_account"])
            ):
                bank_account_id = self.d[getKey(ba, invoice["bank_account"])]
            account_id = self.d[getKey(aa, invoice["account"])]
            move_id = False
            if invoice["move"]:
                move_id = self.d[getKey(am, invoice["move"])]
            partner_id = self.d[getKey(pa, invoice["invoice_address"])]
            payment_type_id = False
            if invoice["payment_type"]:
                payment_type_id = self.PAYMENT_MODES_MAP[str(invoice["payment_type"])]
            payment_term_id = False
            if invoice["payment_term"]:
                payment_term_id = self.PAYMENT_TERM_MAP[str(invoice["payment_term"])]

            vals = {
                "comment": (invoice["comment"] and invoice["comment"] != "''")
                and invoice["comment"]
                or False,
                "reference": (invoice["reference"] and invoice["reference"] != "''")
                and invoice["reference"]
                or False,
                "payment_term": payment_term_id,
                "move_id": move_id,
                "number": invoice["number"] or False,
                "invoice_number": invoice["number"] or False,
                "supplier_invoice_number": invoice["description"] or False,
                "partner_id": partner_id,
                "type": INV_TYPE_MAP[invoice["type"]],
                "journal_id": journal_id,
                "account_id": account_id,
                "date_invoice": invoice["invoice_date"]
                and format_date(invoice["invoice_date"])
                or False,
                "payment_mode_id": payment_type_id,
                "partner_bank_id": bank_account_id,
            }
            print "vals: ", vals
            invoice_id = self.odoo.create("account.invoice", vals)
            self.d[getKey(ai, invoice["id"])] = invoice_id

            self.crT.execute(
                "select id,sequence,unit,gross_unit_price,note,"
                "product,description,account,quantity,"
                "discount from account_invoice_line where "
                "invoice = %s" % (invoice["id"])
            )
            lines_data = self.crT.fetchall()
            for line in lines_data:
                product_id = False
                if line["product"]:
                    product_id = self.d[getKey(pt, line["product"])]
                account_id = self.d[getKey(aa, line["account"])]
                uos_id = 1  # Unidad
                if line["unit"]:
                    uos_id = self.d[getKey(pu, line["unit"])]
                line_vals = {
                    "product_id": product_id,
                    "account_id": account_id,
                    "name": line["description"]
                    + (
                        (line["note"] and line["note"] != "''")
                        and ("\n" + line["note"])
                        or ""
                    ),
                    "quantity": float(line["quantity"]),
                    "sequence": line["sequence"] or 0.0,
                    "discount": line["discount"] and float(line["discount"]) or 0.0,
                    "price_unit": float(line["gross_unit_price"]),
                    "invoice_id": invoice_id,
                    "uos_id": uos_id,
                }
                self.crT.execute(
                    "select tax from account_invoice_line_account_tax "
                    "where line = %s" % (line["id"])
                )
                taxes_data = self.crT.fetchall()
                taxes_ids = []
                for tax in taxes_data:
                    tax_id = self.TAXES_MAP[str(tax["tax"])]
                    taxes_ids.extend(tax_id)
                if taxes_ids:
                    line_vals["invoice_line_tax_id"] = [(6, 0, taxes_ids)]
                print "line_vals: ", line_vals
                line_id = self.odoo.create("account.invoice.line", line_vals)
                self.d[getKey(ail, line["id"])] = line_id

            self.odoo.execute("account.invoice", "button_reset_taxes", [invoice_id])
            if invoice["state"] not in ("draft", "cancel", "validated"):
                self.odoo.exec_workflow("account.invoice", "invoice_open", invoice_id)
            elif invoice["state"] == "cancel" and not move_id:
                self.odoo.exec_workflow("account.invoice", "invoice_cancel", invoice_id)
            elif invoice["state"] == "validated":
                self.odoo.exec_workflow(
                    "account.invoice", "invoice_proforma2", invoice_id
                )
        return True

    def migrate_account_bank_statements(self):
        self.crT.execute(
            "select abs.id,end_date,absj.journal,start_balance,"
            "date,end_balance,state from account_bank_statement "
            "abs inner join account_bank_statement_journal absj "
            "on absj.id = abs.journal"
        )
        data = self.crT.fetchall()
        bs = "account_bank_statement"
        bsl = "account_bank_statement_line"
        aj = "account_journal"
        pp = "party_party"
        aa = "account_account"
        am = "account_move"
        aml = "account_move_line"
        STATE_MAP = {"confirmed": "confirm"}
        self.crO.execute("update account_move_line set statement_id = NULL")
        self.crO.execute("delete from account_bank_statement_line")
        self.crO.execute("delete from account_bank_statement")
        self.close_crO()
        for statement in data:
            journal_id = self.d[getKey(aj, statement["journal"])]
            acc_date = format_date(statement["date"])
            period_id = self.odoo.execute("account.period", "find", acc_date)
            vals = {
                "journal_id": journal_id,
                "period_id": period_id[0],
                "state": STATE_MAP[statement["state"]],
                "balance_end_real": statement["end_balance"]
                and float(statement["end_balance"])
                or 0.0,
                "balance_start": statement["start_balance"]
                and float(statement["start_balance"])
                or 0.0,
                "date": acc_date,
            }
            print "vals: ", vals
            bs_id = self.odoo.create("account.bank.statement", vals)
            self.d[getKey(bs, statement["id"])] = bs_id
            move_line_ids = []
            self.crT.execute(
                "select account,absml.description,move,"
                "coalesce(absml.amount,absl.amount) as amount,"
                "absl.date,party,notes,absl.id "
                "from account_bank_statement_line absl left "
                "join account_bank_statement_move_line absml on "
                "absl.id = absml.line where statement = %s" % (statement["id"])
            )
            lines_data = self.crT.fetchall()
            for line in lines_data:
                account_id = False
                if line["account"]:
                    print "account: ", line["account"]
                    account_id = self.d[getKey(aa, line["account"])]
                partner_id = False
                if line["party"]:
                    print "party: ", line["party"]
                    partner_id = self.d[getKey(pp, line["party"])]
                journal_entry_id = False
                if line["move"]:
                    print "move: ", line["move"]
                    journal_entry_id = self.d[getKey(am, line["move"])]
                line_vals = {
                    "name": line["description"] or "-",
                    "date": format_date(line["date"]),
                    "amount": line["amount"] and float(line["amount"]) or 0.0,
                    "partner_id": partner_id,
                    "account_id": account_id,
                    "statement_id": bs_id,
                    "note": line["notes"] or "",
                    "journal_entry_id": journal_entry_id,
                }
                print "line_vals: ", line_vals
                absl_id = self.odoo.create("account.bank.statement.line", line_vals)
                self.d[getKey(bsl, line["id"])] = absl_id
                self.crT.execute(
                    "select move_line from "
                    "account_bank_reconciliation where "
                    "bank_statement_line = %s" % (line["id"])
                )
                reconcile_data = self.crT.fetchall()
                for reconcile in reconcile_data:
                    move_line_id = self.d[getKey(aml, reconcile["move_line"])]
                    line_data = self.odoo.read("account.move.line", move_line_id, [])
                    if line_data:
                        move_line_ids.append(move_line_id)
            if move_line_ids:
                self.odoo.write(
                    "account.move.line", move_line_ids, {"statement_id": bs_id}
                )
        print "end_bank_statement"
        return True

    def migrate_stock_lots(self):
        self.crT.execute(
            "select id,product,number,life_date,removal_date,"
            "expiry_date,alert_date,lot_date,active,"
            "write_date,create_date from "
            "stock_lot"
        )
        data = self.crT.fetchall()
        pp = "product_product"
        sl = "stock_lot"
        for lot in data:
            tr_date = lot["write_date"] or lot["create_date"]
            if tr_date < self.last_update:
                continue

            update = False
            if self.d.has_key(getKey(sl, lot["id"])):
                update = True

            product_id = self.d[getKey(pp, lot["product"])]
            vals = {
                "name": lot["number"],
                "product_id": product_id,
                "create_date": format_date(lot["lot_date"]),
                "life_date": lot["life_date"]
                and format_date(lot["life_date"])
                or False,
                "removal_date": lot["removal_date"]
                and format_date(lot["removal_date"])
                or False,
                "alert_date": lot["alert_date"]
                and format_date(lot["alert_date"])
                or False,
                "use_date": lot["expiry_date"]
                and format_date(lot["expiry_date"])
                or False,
            }
            if not update:
                print "create vals: ", vals
                lot_id = self.odoo.create("stock.production.lot", vals)
                self.d[getKey(sl, lot["id"])] = lot_id
            else:
                print "update vals: ", vals
                lot_id = self.d[getKey(sl, lot["id"])]
                self.odoo.write("stock.production.lot", [lot_id], vals)
        return True

    def migrate_inventories(self):
        self.crT.execute("select id,state,date,location from " "stock_inventory")
        data = self.crT.fetchall()
        st = "stock_inventory"
        stl = "stock_inventory_line"
        pp = "product_product"
        sl = "stock_lot"
        for inventory in data:
            if self.d.has_key(getKey(st, inventory["id"])):
                continue
            location_id = self.LOCATIONS_MAP[str(inventory["location"])]
            vals = {
                "name": format_date(inventory["date"]),
                "location_id": location_id,
                "date": format_date(inventory["date"]),
                "filter": "partial",
                "state": inventory["state"],
            }
            print "vals: ", vals
            inv_id = self.odoo.create("stock.inventory", vals)
            self.d[getKey(st, inventory["id"])] = inv_id
            self.crT.execute(
                "select id,product,expected_quantity,quantity,"
                "lot from stock_inventory_line where "
                "inventory = %s" % (inventory["id"])
            )
            lines_data = self.crT.fetchall()
            for line in lines_data:
                product_id = self.d[getKey(pp, line["product"])]
                product_data = self.odoo.read("product.product", product_id, ["uom_id"])
                lot_id = False
                if line["lot"]:
                    lot_id = self.d[getKey(sl, line["lot"])]
                line_vals = {
                    "product_id": product_id,
                    "inventory_id": inv_id,
                    "location_id": location_id,
                    "product_uom_id": product_data["uom_id"][0],
                    "product_qty": float(line["quantity"]),
                    "prod_lot_id": lot_id,
                }
                print "line_vals: ", line_vals
                line_id = self.odoo.create("stock.inventory.line", line_vals)
                self.d[getKey(stl, line["id"])] = line_id
        return True

    def migrate_moves(self):
        self.crT.execute(
            "select id,create_date,origin,planned_date,unit_price"
            ",state,effective_date,cost_price,internal_quantity,"
            "uom,quantity,product,to_location,from_location,lot,"
            "write_date "
            "from stock_move order by id asc"
        )
        data = self.crT.fetchall()
        print "migrate_moves"
        sm = "stock_move"
        pu = "product_uom"
        pp = "product_product"
        sl = "stock_lot"
        stl = "stock_inventory_line"
        for move in data:
            tr_date = move["write_date"] or move["create_date"]
            if tr_date < self.last_update:
                continue
            if self.d.has_key(getKey(sm, move["id"])):
                move_id = self.d[getKey(sm, move["id"])]
                move_data = self.odoo.read("stock.move", move_id, ["state"])
                if move_data:
                    if move_data["state"] == "done":
                        continue
                    else:
                        self.odoo.write("stock.move", [move_id], {"state": "draft"})
                        self.odoo.unlink("stock.move", [move_id])
            product_id = self.d[getKey(pp, move["product"])]
            product_data = self.odoo.read("product.product", product_id, ["uom_id"])
            uom_id = self.d[getKey(pu, move["uom"])]
            location_id = self.LOCATIONS_MAP[str(move["from_location"])]
            location_dest_id = self.LOCATIONS_MAP[str(move["to_location"])]
            restrict_lot_id = False
            if move["lot"]:
                restrict_lot_id = self.d[getKey(sl, move["lot"])]
            inventory_id = False
            if move["origin"] and move["origin"].startswith("stock.inventory.line"):
                if self.d.has_key(getKey(stl, int(move["origin"].split(",")[1]))):
                    sil_id = self.d[getKey(stl, int(move["origin"].split(",")[1]))]
                    sil_data = self.odoo.read(
                        "stock.inventory.line", sil_id, ["inventory_id"]
                    )
                    inventory_id = sil_data["inventory_id"][0]
            vals = {
                "name": "-",
                "date_expected": move["planned_date"]
                and format_date(move["planned_date"])
                or format_date(move["create_date"]),
                "product_id": product_id,
                "product_uom_qty": float(move["internal_quantity"]),
                "product_uom": product_data["uom_id"][0],
                "product_uos_qty": float(move["quantity"]),
                "product_uos": uom_id,
                "location_id": location_id,
                "location_dest_id": location_dest_id,
                "price_unit": move["unit_price"] and float(move["unit_price"]) or 0.0,
                "procure_method": "make_to_stock",
                "inventory_id": inventory_id,
                "restrict_lot_id": restrict_lot_id,
            }
            print "vals: ", vals
            move_id = self.odoo.create("stock.move", vals)
            self.d[getKey(sm, move["id"])] = move_id

            if move["state"] == "cancel":
                self.odoo.execute("stock.move", "action_cancel", [move_id])
            elif move["state"] == "done":
                self.odoo.execute("stock.move", "action_done", [move_id])
                if move["effective_date"]:
                    self.odoo.write(
                        "stock.move",
                        [move_id],
                        {"date": format_date(move["effective_date"])},
                    )
            elif move["state"] == "assigned":
                self.odoo.execute("stock.move", "force_assign", [move_id])

            if move["cost_price"] or move["effective_date"]:
                move_data = self.odoo.read("stock.move", move_id, ["quant_ids"])
                if move_data["quant_ids"]:
                    print "QUANTS: ", move_data["quant_ids"]
                    for quant in move_data["quant_ids"]:
                        qvals = {"in_date": format_date(move["effective_date"])}
                        if move["cost_price"]:
                            qvals["cost"] = float(move["cost_price"])
                        self.odoo.write("stock.quant", [quant], qvals)
        return True

    def merge_quants(self):
        move_ids = self.odoo.search(
            "stock.move",
            [
                ("state", "=", "done"),
                ("location_dest_id.usage", "=", "internal"),
                ("product_id.type", "=", "product"),
            ],
            order="date",
        )
        print "len(moves): ", len(move_ids)
        for move in move_ids:
            move_data = self.odoo.read("stock.move", move, ["quant_ids"])
            if move_data["quant_ids"]:
                print "len(quants): ", len(move_data["quant_ids"])
                quants_data = self.odoo.read(
                    "stock.quant", move_data["quant_ids"], ["qty"]
                )
                quant_ids = []
                for quant in quants_data:
                    if quant["qty"] > 0:
                        quant_ids.append(quant["id"])
                if quant_ids:
                    print "len(valid_quants): ", len(quant_ids)
                    for quant in quant_ids:
                        self.odoo.execute(
                            "stock.quant", "quants_reconcile_negative", quant, move
                        )
        return True

    def migrate_pickings(self):
        if self.esale:
            self.crT.execute(
                "select id,code,planned_date,contact_address as "
                "address_id,effective_date,supplier as partner_id,"
                "comment,'stock_shipment_in' as table,"
                "create_date,write_date from stock_shipment_in "
                "union select id,code,planned_date,delivery_address "
                "as address_id,effective_date,customer as partner_id,"
                "comment,'stock_shipment_out_return' as "
                "table,create_date,write_date from "
                "stock_shipment_out_return union select id,"
                "code,planned_date,delivery_address as address_id,"
                "effective_date,customer as partner_id,comment,"
                "'stock_shipment_out' as table,create_date,write_date "
                "from stock_shipment_out "
                "union select id,code,planned_date,null as address_id,"
                "effective_date,null as partner_id,comment,"
                "'stock_shipment_in_return' as table,"
                "create_date,write_date from "
                "stock_shipment_in_return union select id,code,"
                "planned_date,null as address_id,effective_date,"
                "null as partner_id,comment,'stock_shipment_internal' "
                "as table,create_date,write_date from "
                "stock_shipment_internal"
            )
        else:
            self.crT.execute(
                "select id,'IN/' || code as code,planned_date,"
                "contact_address as address_id,effective_date,supplier "
                "as partner_id,comment,'stock_shipment_in' as table,"
                "create_date,write_date from stock_shipment_in union "
                "select id,'ROUT/' || code as code,planned_date,"
                "delivery_address as address_id,effective_date,"
                "customer as partner_id,comment,"
                "'stock_shipment_out_return' as table,"
                "create_date,write_date from stock_shipment_out_return"
                " union select id,'OUT/' || code as code,planned_date,"
                "delivery_address as address_id,effective_date,"
                "customer as partner_id,comment,'stock_shipment_out'"
                " as table,create_date,write_date from "
                "stock_shipment_out union select id,'RIN/' || code "
                "as code,planned_date,null as address_id,"
                "effective_date,null as partner_id,comment,"
                "'stock_shipment_in_return' as table,create_date,"
                "write_date from stock_shipment_in_return union "
                "select id, 'INT/' || code as code,planned_date,null "
                "as address_id,effective_date,null as partner_id,"
                "comment,'stock_shipment_internal' as table,"
                "create_date,write_date from stock_shipment_internal"
            )
        data = self.crT.fetchall()
        pa = "party_address"
        sm = "stock_move"
        TYPE_MAP = {
            "stock_shipment_in": "incoming",
            "stock_shipment_out_return": "incoming",
            "stock_shipment_out": "outgoing",
            "stock_shipment_in_return": "outgoing",
            "stock_shipment_internal": "internal",
        }
        for pick in data:
            tr_date = pick["write_date"] or pick["create_date"]
            if tr_date < self.last_update:
                continue

            if self.d.has_key(getKey(pick["table"], pick["id"])):
                pick_id = self.d[getKey(pick["table"], pick["id"])]
                pick_data = self.odoo.read("stock.picking", pick_id, ["state"])
                if pick_data:
                    if pick_data["state"] == "done":
                        continue
                    else:
                        move_ids = self.odoo.search(
                            "stock.move", [("picking_id", "=", pick_id)]
                        )
                        if move_ids:
                            self.odoo.write(
                                "stock.move", move_ids, {"picking_id": False}
                            )
                        self.odoo.unlink("stock.picking", [pick_id])
            picking_type_id = self.odoo.search(
                "stock.picking.type", [("code", "=", TYPE_MAP[pick["table"]])]
            )[0]
            partner_id = False
            if pick["address_id"]:
                try:
                    partner_id = self.d[getKey(pa, pick["address_id"])]
                except:
                    partner_id = False
            vals = {
                "name": pick["code"],
                "note": pick["comment"] or "",
                "move_type": "one",
                "date_done": pick["effective_date"]
                and format_date(pick["effective_date"])
                or False,
                "partner_id": partner_id,
                "picking_type_id": picking_type_id,
            }
            print "PICK vals: ", vals
            pick_id = self.odoo.create("stock.picking", vals)
            self.d[getKey(pick["table"], pick["id"])] = pick_id

            model = pick["table"].replace("_", ".")
            ref = model + "," + str(pick["id"])
            self.crT.execute(
                "select id from stock_move where " "shipment = '%s'" % (ref)
            )
            moves_data = self.crT.fetchall()
            move_ids = []
            for move in moves_data:
                move_id = self.d[getKey(sm, move["id"])]
                move_ids.append(move_id)
            if move_ids:
                self.odoo.write(
                    "stock.move",
                    move_ids,
                    {
                        "picking_id": pick_id,
                        "picking_type_id": picking_type_id,
                        "partner_id": partner_id,
                    },
                )
        return True

    def migrate_orderpoints(self):
        self.crT.execute(
            "select id,product,min_quantity,max_quantity,"
            "create_date,write_date from "
            "stock_order_point"
        )
        data = self.crT.fetchall()
        sop = "stock_order_point"
        pp = "product_product"
        warehouse_id = self.odoo.search("stock.warehouse", [], limit=1)[0]
        wh_data = self.odoo.read("stock.warehouse", warehouse_id, ["lot_stock_id"])
        for op in data:
            tr_date = op["write_date"] or op["create_date"]
            if tr_date < self.last_update:
                continue

            update = False
            if self.d.has_key(getKey(sop, op["id"])):
                update = True

            vals = {
                "product_id": self.d[getKey(pp, op["product"])],
                "warehouse_id": warehouse_id,
                "location_id": wh_data["lot_stock_id"][0],
                "product_min_qty": float(op["min_quantity"]),
                "product_max_qty": float(op["max_quantity"]),
            }
            if not update:
                op_id = self.odoo.create("stock.warehouse.orderpoint", vals)
                self.d[getKey(sop, op["id"])] = op_id
            else:
                op_id = self.d[getKey(sop, op["id"])]
                self.odoo.write("stock.warehouse.orderpoint", [op_id], vals)

        return True

    def migrate_prestashop_metadata(self):
        self.crT.execute("select id,name,uri,key from prestashop_app")
        backend_data = self.crT.fetchall()
        pa = "prestashop_app"
        for backend_line in backend_data:
            vals = {
                "version": "1.5",
                "name": backend_line["name"],
                "location": backend_line["uri"],
                "webservice_key": backend_line["key"],
                "warehouse_id": self.odoo.search("stock.warehouse", [], limit=1)[0],
            }
            backend_id = self.odoo.create("prestashop.backend", vals)
            self.d[getKey(pa, backend_line["id"])] = backend_id
        return True

    def migrate_carrier(self):
        self.crT.execute(
            "select id,party,carrier_product,create_date," "write_date from carrier"
        )
        carrier_data = self.crT.fetchall()
        p = "party_party"
        prod = "product_product"
        for carrier_line in carrier_data:
            if self.d.has_key(getKey("carrier", carrier_line["id"])):
                tr_date = carrier_line["write_date"] or carrier_line["create_date"]
                if tr_date <= self.last_update:
                    continue
            partner_id = self.d[getKey(p, carrier_line["party"])]
            product_id = self.d[getKey(prod, carrier_line["carrier_product"])]
            name = "%s - %s" % (
                self.odoo.read("res.partner", partner_id, ["name"])["name"],
                self.odoo.read("product.product", product_id, ["name"])["name"],
            )
            vals = {
                "partner_id": partner_id,
                "product_id": product_id,
                "name": name,
            }
            if self.esale:
                self.crT.execute(
                    "select code from esale_carrier where carrier=%s"
                    % carrier_line["id"]
                )
                codes = [x[0] for x in self.crT.fetchall()]
                codes = ",".join(codes)
                vals["magento_code"] = codes

            if self.d.has_key(getKey("carrier", carrier_line["id"])):
                self.odoo.write(
                    "delivery.carrier",
                    [self.d[getKey("carrier", carrier_line["id"])]],
                    vals,
                )
            else:
                carrier_id = self.odoo.create("delivery.carrier", vals)
                self.d[getKey("carrier", carrier_line["id"])] = carrier_id
                self.odoo.unlink("delivery.grid", self.odoo.search("delivery.grid", []))

    def migrate_carrier_api(self):
        self.crT.execute(
            "select id,reference_origin,weight,reference,"
            "create_date,write_date,"
            "username,method,phone,debug,password,zips,vat,"
            "weight_unit,weight_api_unit,envialia_agency from "
            "carrier_api"
        )
        api_data = self.crT.fetchall()
        for api_line in api_data:
            if self.d.has_key(getKey("carrier_api", api_line["id"])):
                tr_date = api_line["write_date"] or api_line["create_date"]
                if tr_date <= self.last_update:
                    continue
            vals = {
                "method": api_line["method"],
                "username": api_line["username"],
                "password": api_line["password"],
                "debug": api_line["debug"],
                "reference": api_line["reference"],
                "reference_origin": api_line["reference_origin"],
                "weight": api_line["weight"],
                "vat": api_line["vat"],
                "phone": api_line["phone"],
                "zips": api_line["zips"],
                "envialia_agency": api_line["envialia_agency"]
                and api_line["envialia_agency"]
                or False,
                "weight_unit": api_line["weight_unit"]
                and self.UOM_MAP[str(api_line["weight_unit"])]
                or False,
                "weight_api_unit": api_line["weight_api_unit"]
                and self.UOM_MAP[str(api_line["weight_api_unit"])]
                or False,
                "company_id": 1,
            }
            self.crT.execute(
                "select carrier from carrier_api_carrier_rel "
                "where api=%s" % api_line["id"]
            )
            carriers = self.crT.fetchall()
            vals["carriers"] = [
                (6, 0, [self.d[getKey("carrier", x["carrier"])] for x in carriers])
            ]
            if self.d.has_key(getKey("carrier_api", api_line["id"])):
                self.odoo.write(
                    "carrier.api", [self.d[getKey("carrier_api", api_line["id"])]], vals
                )
            else:
                api_id = self.odoo.create("carrier.api", vals)
                self.d[getKey("carrier_api", api_line["id"])] = api_id

    def migrate_carrier_api_services(self):
        self.crT.execute("select id,code,name,api from carrier_api_service")
        service_data = self.crT.fetchall()
        for service_line in service_data:
            vals = {
                "code": service_line["code"],
                "name": service_line["name"],
                "carrier_api": self.d[getKey("carrier_api", service_line["api"])],
            }
            if self.d.has_key(getKey("carrier_api_service", service_line["id"])):
                self.odoo.write(
                    "carrier.api.service",
                    [self.d[getKey("carrier_api_service", service_line["id"])]],
                    vals,
                )
            else:
                service_id = self.odoo.create("carrier.api.service", vals)
                self.d[getKey("carrier_api_service", service_line["id"])] = service_id

    def migrate_carrier_data(self):
        self.crT.execute(
            "select id,carrier_service,asm_return,carrier_notes,"
            "carrier from party_party"
        )
        partner_data = self.crT.fetchall()
        for partner in partner_data:
            service = False
            carrier = False
            odoo_partner = self.d[getKey("party_party", partner["id"])]
            if partner["carrier"]:
                carrier = self.d[getKey("carrier", partner["carrier"])]
            if partner["carrier_service"]:
                service = self.d[
                    getKey("carrier_api_service", partner["carrier_service"])
                ]
            partner_vals = {
                "asm_return": partner["asm_return"] or False,
                "property_delivery_carrier": carrier,
                "carrier_service_id": service,
                "carrier_notes": partner["carrier_notes"] or False,
            }
            self.odoo.write("res.partner", odoo_partner, partner_vals)
        self.crT.execute(
            "select id,carrier,weight,number_packages,"
            "carrier_service,carrier_delivery,carrier_printed,"
            "carrier_notes,carrier_send_date,asm_return,"
            "carrier_tracking_ref from stock_shipment_out"
        )
        picking_data = self.crT.fetchall()
        for picking in picking_data:
            picking_vals = {
                "weight_edit": picking["weight"] or 0.0,
                "number_of_packages": picking["number_packages"] or 0,
                "asm_return": picking["asm_return"] or False,
                "carrier_tracking_ref": picking["carrier_tracking_ref"] or "",
                "carrier_notes": picking["carrier_notes"] or "",
                "carrier_printed": picking["carrier_printed"] or False,
                "carrier_delivery": picking["carrier_delivery"] or False,
            }
            picking_vals["carrier_send_date"] = (
                picking["carrier_send_date"]
                and picking["carrier_send_date"].strftime("%Y-%m-%d %H:%M:%S")
                or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            if picking["carrier"]:
                picking_vals["carrier_id"] = self.d[
                    getKey("carrier", picking["carrier"])
                ]
            if picking["carrier_service"]:
                picking_vals["carrier_service"] = self.d[
                    getKey("carrier_api_service", picking["carrier_service"])
                ]
            self.odoo.write(
                "stock.picking",
                self.d[getKey("stock_shipment_out", picking["id"])],
                picking_vals,
            )

    def migrate_magento_carrier(self):
        init_carrier_code = "owebiashipping1_"

        def lines_per_n(f, n):
            for line in f:
                yield "".join(chain([line], islice(f, n - 1)))

        file_data = []
        with open("data/shipment.json") as f:
            for chunk in lines_per_n(f, 10):
                try:
                    jfile = yaml.load(chunk)
                    file_data.append(jfile)
                except:
                    pass
        created_destinations = {}
        self.odoo.unlink("delivery.grid", self.odoo.search("delivery.grid", []))
        for ship_grid in file_data:
            append = False
            destination_vals = ship_grid["destination"].split("(")
            country_code = destination_vals[0]
            prov_names = False
            if len(destination_vals) > 1 and "-" not in country_code:
                prov_names = destination_vals[1]
            if prov_names:
                dict_key = country_code + prov_names.replace(")", "")
            else:
                dict_key = country_code
            if dict_key in created_destinations:
                append = True
                grid_vals = created_destinations[dict_key]
            if not append:
                grid_vals = {"name": ship_grid["label"], "line_ids": []}
                carrier_id = self.odoo.search(
                    "delivery.carrier",
                    [("magento_code", "like", init_carrier_code + ship_grid["code"])],
                )
                if not carrier_id:
                    carrier_id = self.odoo.search("delivery.carrier", [])
                    print "%s -- %s" % (carrier_id[0], ship_grid["code"])
                grid_vals["carrier_id"] = carrier_id[0]

                country = self.odoo.search("res.country", [("code", "=", country_code)])
                grid_vals["country_ids"] = [(4, country[0])]
                if prov_names:
                    grid_vals["state_ids"] = []
                    provs = prov_names.replace(")", "").split(",")
                    for prov in provs:
                        prov_odoo = self.odoo.search(
                            "res.country.state", [("name", "ilike", prov)]
                        )
                        grid_vals["state_ids"].append((4, prov_odoo[0]))
                else:
                    # se da mayor secuencia a la regla generalista.
                    grid_vals["sequence"] = 20
            condition = ship_grid["conditions"].split("and")[0].split("}")[1].lstrip()
            operator = condition[:2].lstrip().rstrip()
            quantity = float(condition[2:].lstrip())
            grid_vals["line_ids"].append(
                (
                    0,
                    0,
                    {
                        "name": ship_grid["name"],
                        "price_type": "fixed",
                        "list_price": ship_grid["fees"],
                        "type": "price",
                        "operator": operator,
                        "max_value": quantity,
                        "standard_price": 0,
                    },
                )
            )

            created_destinations[dict_key] = grid_vals
        for vals_k in created_destinations:
            vals = created_destinations[vals_k]
            self.odoo.create("delivery.grid", vals)

    def migrate_commission_plan(self):
        self.crT.execute("select id,name from commission_plan")
        plan_data = self.crT.fetchall()
        self.crO.execute("delete from sale_agent_plan_line")
        self.crO.execute("delete from sale_agent_plan")
        self.close_crO()
        for plan in plan_data:
            plan_vals = {"name": plan["name"]}
            self.crT.execute(
                "select id,product,substring(formula from 8 for "
                "5) as formula from commission_plan_line "
                "where plan=%s" % plan["id"]
            )
            plan_lines = self.crT.fetchall()
            lines = []
            for line in plan_lines:
                odoo_product_id = False
                if line["product"]:
                    odoo_product_id = self.d[getKey("product_product", line["product"])]
                commission_perc = float(line["formula"])
                commission = self.odoo.search(
                    "sale.commission", [("fix_qty", "=", commission_perc)]
                )
                if not commission:
                    commission = self.odoo.create(
                        "sale.commission",
                        {
                            "name": "%s%%" % commission_perc,
                            "fix_qty": commission_perc,
                            "active": True,
                            "type": "fixed",
                            "amount_base_type": "gross_amount",
                            "invoice_state": "open",
                        },
                    )
                else:
                    commission = commission[0]
                lines.append(
                    (0, 0, {"product": odoo_product_id, "commission": commission})
                )
            plan_vals["lines"] = lines
            plan_id = self.odoo.create("sale.agent.plan", plan_vals)
            self.d[getKey("commission_plan", plan["id"])] = plan_id

    def migrate_commission_agent(self):
        self.crT.execute("select id,party,plan from commission_agent")
        agent_data = self.crT.fetchall()
        for agent in agent_data:
            if not agent["plan"]:
                continue
            partner_id = self.d[getKey("party_party", agent["party"])]
            plan_id = self.d[getKey("commission_plan", agent["plan"])]
            self.odoo.write("res.partner", partner_id, {"agent": True, "plan": plan_id})

            self.crT.execute(
                "select party from party_commission_agent "
                "where agent=%s" % agent["id"]
            )
            partner_ids = self.crT.fetchall()
            odoo_partners = []
            for tr_partner_id in partner_ids:
                if not agent["plan"]:
                    continue
                odoo_partner_id = self.d[getKey("party_party", tr_partner_id["party"])]
                odoo_partners.append(odoo_partner_id)
            self.odoo.write("res.partner", odoo_partners, {"agents": [(4, partner_id)]})

    def migrate_users(self):
        self.crT.execute(
            "select id,name,login,active,email,signature from "
            "res_user where login != 'admin'"
        )
        user_data = self.crT.fetchall()
        for user in user_data:
            if "cron" in user["name"].lower():
                continue
            vals = {
                "name": user["name"],
                "login": user["login"],
                "password": "1",
                "lang": "es_ES",
                "tz": "Europe/Madrid",
                "signature": user["signature"] or False,
                "active": user["active"],
                "email": user["email"] or False,
            }
            if self.d.has_key(getKey("res_user", user["id"])):
                self.odoo.write(
                    "res.users", [self.d[getKey("res_user", user["id"])]], vals
                )
            else:
                user_id = self.odoo.create("res.users", vals)
                self.d[getKey("res_user", user["id"])] = user_id

    def migrate_groups(self):
        self.crT.execute(
            "select rurg.user as user, rurg.group as group from "
            '"res_user-res_group" as rurg'
        )
        group_data = self.crT.fetchall()
        for group in group_data:
            if str(group["group"]) not in self.GROUPS_MAP or not self.d.has_key(
                getKey("res_user", group["user"])
            ):
                continue
            vals = {"groups_id": [(4, self.GROUPS_MAP[str(group["group"])])]}
            self.odoo.write(
                "res.users", self.d[getKey("res_user", group["user"])], vals
            )

    def migrate_product_suppliers(self):
        self.crT.execute(
            "select id,delivery_time,product,code,name,sequence,"
            "party from  purchase_product_supplier"
        )
        supplier_data = self.crT.fetchall()
        self.crO.execute("delete from product_supplierinfo")
        self.close_crO()
        for supplier in supplier_data:
            self.crT.execute(
                "select id from product_product where "
                "template=%s" % supplier["product"]
            )
            products = self.crT.fetchall()
            pp_id = self.d[getKey("product_product", products[0][0])]
            product_template = self.odoo.read(
                "product.product", pp_id, ["product_tmpl_id"]
            )
            vals = {
                "product_name": supplier["name"] or False,
                "product_code": supplier["code"] or False,
                "sequence": supplier["sequence"] or False,
                "min_qty": 0,
                "delay": supplier["delivery_time"] or 0,
                "name": self.d[getKey("party_party", supplier["party"])],
                "product_tmpl_id": product_template["product_tmpl_id"][0],
            }
            self.odoo.create("product.supplierinfo", vals)

    def migrate_pricelist(self):
        self.crT.execute("select id,name from product_price_list")
        pricelist_data = self.crT.fetchall()
        for pricelist in pricelist_data:
            vals = {
                "name": pricelist["name"],
                "type": "sale",
                "active": True,
            }
            if self.esale:
                self.crT.execute(
                    "select id,product,sequence,price_list,"
                    "formula,product,quantity,category "
                    "from product_price_list_line where party "
                    "is null and price_list = %s" % pricelist["id"]
                )
            else:
                self.crT.execute(
                    "select id,product,sequence,price_list,"
                    "formula,product,quantity,category "
                    "from product_price_list_line where "
                    "price_list = %s" % pricelist["id"]
                )
            pricelist_line_data = self.crT.fetchall()
            lines = []
            for pricelist_line in pricelist_line_data:
                line_vals = {
                    "min_quantity": pricelist_line["quantity"] or 0,
                }
                if pricelist_line["product"]:
                    line_vals["sequence"] = 1
                    line_vals["product_id"] = self.d[
                        getKey("product_product", pricelist_line["product"])
                    ]
                elif pricelist_line["category"]:
                    line_vals["sequence"] = 10
                    line_vals["categ_id"] = self.d[
                        getKey("product_category", pricelist_line["category"])
                    ]
                else:
                    line_vals["sequence"] = 30

                formula = pricelist_line["formula"]
                if formula == "unit_price":
                    line_vals["base"] = 1
                elif "unit_price*(1" in formula:
                    line_vals["base"] = 1
                    line_vals["price_discount"] = float(
                        formula.replace("unit_price*(1", "").replace(")", "")
                    )
                elif "Decimal(round(" in formula:
                    line_vals["base"] = 2
                    line_vals["price_discount"] = (
                        float(
                            formula.replace(
                                "Decimal(round(product.cost_price*", ""
                            ).replace(",2))", "")
                        )
                        - 1
                    )
                elif "compute_price_list(" in formula:
                    line_vals["base"] = -1
                    line_vals["name"] = "manual"
                elif "unit_price*" in formula:
                    line_vals["base"] = 1

                else:
                    line_vals["base"] = 1
                    line_vals["price_discount"] = -1
                    line_vals["price_surcharge"] = float(formula)

                lines.append((0, 0, line_vals))
            version_vals = []
            if self.d.has_key(getKey("product_price_list", pricelist["id"])):
                versions = self.odoo.search(
                    "product.pricelist.version",
                    [
                        (
                            "pricelist_id",
                            "=",
                            self.d[getKey("product_price_list", pricelist["id"])],
                        )
                    ],
                )
                for version in versions:
                    version_vals.append((2, version))
            version_vals.append(
                (0, 0, {"name": "default", "active": True, "items_id": lines})
            )
            vals["version_id"] = version_vals
            if self.d.has_key(getKey("product_price_list", pricelist["id"])):
                self.odoo.write(
                    "product.pricelist",
                    [self.d[getKey("product_price_list", pricelist["id"])]],
                    vals,
                )
            else:
                pricelist_id = self.odoo.create("product.pricelist", vals)
                self.d[getKey("product_price_list", pricelist["id"])] = pricelist_id

    def sync_shops(self):
        self.crT.execute("select id,name,active " "from sale_shop order by active asc")
        shop_data = self.crT.fetchall()
        ss = "sale_shop"
        for shop in shop_data:
            vals = {"active": shop["active"], "name": shop["name"]}
            shop_ids = self.odoo.search(
                "sale.store",
                [("name", "=", shop["name"]), ("active", "in", [True, False])],
            )
            if not shop_ids:
                shop_id = self.odoo.create("sale.store", vals)
            else:
                shop_id = shop_ids[0]
            self.d[getKey(ss, shop["id"])] = shop_id

    def sync_ecommerce_shops(self):
        self.crT.execute(
            "select ss.id,ss.name,ss.active,logo,pw.name as "
            "prestashop_name,ms.name as magento_name,journal "
            "from sale_shop ss left join magento_storegroup ms "
            "on ss.magento_website = ms.magento_website left join"
            " prestashop_website pw on pw.id = "
            "ss.prestashop_website order by active asc"
        )
        shop_data = self.crT.fetchall()
        ss = "sale_shop"
        aj = "account_journal"
        for shop in shop_data:
            journal_id = (
                shop["journal"] and self.d[getKey(aj, shop["journal"])] or False
            )
            vals = {
                "logo": shop["logo"] and base64.encodestring(shop["logo"]) or False,
                "active": shop["active"],
                "journal_id": journal_id,
            }
            shop_id = False
            if shop["magento_name"]:
                shop_ids = self.odoo.search(
                    "sale.store",
                    [
                        ("name", "=", shop["magento_name"]),
                        ("active", "in", [True, False]),
                    ],
                )
                shop_id = shop_ids and shop_ids[0] or False
            elif shop["prestashop_name"]:
                shop_ids = self.odoo.search(
                    "sale.store",
                    [
                        ("name", "=", shop["prestashop_name"]),
                        ("active", "in", [True, False]),
                    ],
                )
                shop_id = shop_ids and shop_ids[0] or False
            if shop_id:
                self.odoo.write("sale.store", [shop_id], vals)
            else:
                vals["name"] = shop["name"]
                if self.d.has_key(getKey(ss, shop["id"])):
                    shop_id = self.d[getKey(ss, shop["id"])]
                    self.odoo.write("sale.store", [shop_id], vals)
                else:
                    shop_id = self.odoo.create("sale.store", vals)

            self.d[getKey(ss, shop["id"])] = shop_id

    def migrate_purchase_order(self):
        self.crT.execute(
            "select id,comment,reference,payment_term,state,"
            "purchase_date,total_amount_cache,shipment_state,"
            "supplier_reference,invoice_state,invoice_method,"
            "invoice_address,payment_type from purchase_purchase"
        )
        purchase_data = self.crT.fetchall()
        po = "purchase_purchase"
        pl = "purchase_line"
        for purchase in purchase_data:
            if self.d.has_key(getKey(po, purchase["id"])):
                order_data = self.odoo.read(
                    "purchase.order", self.d[getKey(po, purchase["id"])], ["state"]
                )
                if order_data["state"] == "done":
                    continue
                else:
                    self.crO.execute(
                        "delete from purchase_order_line where "
                        "order_id = %s" % self.d[getKey(po, purchase["id"])]
                    )
                    self.crO.execute(
                        "delete from purchase_order where id = %s"
                        % self.d[getKey(po, purchase["id"])]
                    )
                    self.close_crO()
            warehouse_id = self.odoo.search("stock.warehouse", [])
            warehouse_vals = self.odoo.read(
                "stock.warehouse", warehouse_id, ["in_type_id", "wh_input_stock_loc_id"]
            )
            in_loc = warehouse_vals[0]["wh_input_stock_loc_id"][0]
            type_id = warehouse_vals[0]["in_type_id"][0]
            pricelist_id = self.odoo.search(
                "product.pricelist", [("type", "=", "purchase")]
            )
            inv_met_dict = {
                "manual": "manual",
                "order": "order",
                "shipment": "picking",
            }
            purchase_date = (
                purchase["purchase_date"]
                and purchase["purchase_date"].strftime("%Y-%m-%d 00:00:00")
                or datetime.now().strftime("%Y-%m-%d 00:00:00")
            )
            vals = {
                "name": purchase["reference"] or "/",
                "notes": purchase["comment"] or "",
                "partner_id": self.d[
                    getKey("party_address", purchase["invoice_address"])
                ],
                "date_order": purchase_date,
                "picking_type_id": type_id,
                "pricelist_id": pricelist_id[0],
                "partner_ref": purchase["supplier_reference"] or "",
                "invoice_method": inv_met_dict[purchase["invoice_method"]],
                "payment_term_id": purchase["payment_term"]
                and self.PAYMENT_TERM_MAP[str(purchase["payment_term"])]
                or False,
                "payment_mode_id": purchase["payment_type"]
                and self.PAYMENT_MODES_MAP[str(purchase["payment_type"])]
                or False,
                "state": "draft",
                "location_id": in_loc,
            }
            purchase_id = self.odoo.create("purchase.order", vals)
            self.d[getKey(po, purchase["id"])] = purchase_id
            self.crT.execute(
                "select id,sequence,unit,unit_price,product,"
                "description,quantity,discount from "
                "purchase_line where purchase=%s" % purchase["id"]
            )
            purchase_line_data = self.crT.fetchall()
            purchase_lines = []
            for purchase_line in purchase_line_data:
                purchase_lines.append(purchase_line["id"])
                self.crT.execute(
                    "select tax from purchase_line_account_tax "
                    "where line=%s" % purchase_line["id"]
                )
                tax_ids = self.crT.fetchall()
                tax_ids = [x[0] for x in tax_ids]
                if 44 in tax_ids and 77 in tax_ids:
                    tax_ids.remove(77)
                line_vals = {
                    "sequence": purchase_line["sequence"] or False,
                    "name": purchase_line["description"],
                    "price_unit": float(purchase_line["unit_price"]),
                    "product_id": purchase_line["product"]
                    and self.d[getKey("product_product", purchase_line["product"])]
                    or False,
                    "product_qty": purchase_line["quantity"],
                    "discount": float(purchase_line["discount"]),
                    "order_id": self.d[getKey(po, purchase["id"])],
                    "date_planned": purchase_date,
                    "taxes_id": [(4, self.TAXES_MAP[str(x)][0]) for x in tax_ids],
                }
                try:
                    line_vals["product_uom"] = self.UOM_MAP[str(purchase_line["unit"])]
                except KeyError:
                    line_vals["product_uom"] = self.d[
                        getKey("product_uom", purchase_line["unit"])
                    ]
                line_id = self.odoo.create("purchase.order.line", line_vals)
                self.d[getKey(pl, purchase_line["id"])] = line_id
            if purchase["state"] == "cancel":
                self.odoo.execute("purchase.order", "action_cancel", [purchase_id])
            if purchase["state"] in ("processing", "confirmed"):
                self.odoo.exec_workflow(
                    "purchase.order", "purchase_confirm", purchase_id
                )
                picking_ids = self.odoo.read(
                    "purchase.order", [purchase_id], ["picking_ids"]
                )[0]["picking_ids"]
                self.odoo.unlink("stock.picking", picking_ids)
                invoices = []
                for purchase_line in purchase_lines:
                    odoo_purchase_line = self.d[getKey(pl, purchase_line)]
                    self.crT.execute(
                        "select id from stock_move where "
                        "origin='purchase.line,%s'" % purchase_line
                    )
                    move_ids = self.crT.fetchall()
                    for move_id in move_ids:
                        self.odoo.write(
                            "stock.move",
                            self.d[getKey("stock_move", move_id[0])],
                            {"purchase_line_id": odoo_purchase_line},
                        )
                    self.crT.execute(
                        "select id,invoice from "
                        "account_invoice_line where origin = "
                        "'purchase.line,%s'" % purchase_line
                    )
                    invoice_ids = self.crT.fetchall()
                    invoiced = invoice_ids and True or False
                    for invoice in filter(lambda r: r["invoice"], invoice_ids):
                        self.odoo.write(
                            "account.invoice.line",
                            self.d[getKey("account_invoice_line", invoice["id"])],
                            {"purchase_line_id": odoo_purchase_line},
                        )
                        invoices.append(
                            self.d[getKey("account_invoice", invoice["invoice"])]
                        )
                    if invoiced:
                        self.odoo.write(
                            "purchase.order.line",
                            odoo_purchase_line,
                            {"invoiced": True},
                        )
                invoices = list(set(invoices))
                self.odoo.write(
                    "purchase.order", purchase_id, {"invoice_ids": [(6, 0, invoices)]}
                )
                self.odoo.exec_workflow("purchase.order", "picking_ok", purchase_id)

    def migrate_sales(self):
        if self.esale:
            self.crT.execute(
                "select ss.id,comment,reference,payment_term,"
                "sale_date,state,ss.party,ss.create_date,"
                "shipment_address,description,invoice_method,"
                "payment_type,carrier,price_list,shop,"
                "reference_external,sale_discount,esale_coupon,"
                "asm_return,carrier_notes,carrier_service,"
                "invoice_address,ca.party as agent from "
                "sale_sale ss left join commission_agent ca on ca.id ="
                " ss.agent order by ss.id asc"
            )
        else:
            self.crT.execute(
                "select ss.id,comment,reference,payment_term,"
                "sale_date,state,ss.party,ss.create_date,"
                "shipment_address,description,invoice_method,"
                "payment_type,carrier,price_list,shop,sale_discount,"
                "invoice_address,ca.party as agent from sale_sale ss "
                "left join commission_agent ca on ca.id = ss.agent "
                "order by ss.id asc"
            )
        data = self.crT.fetchall()
        PROC_MOVE_STATES_MAP = {
            "done": "done",
            "draft": "confirmed",
            "cancel": "cancel",
            "assigned": "done",
        }
        ss = "sale_sale"
        sl = "sale_line"
        c = "carrier"
        cs = "carrier_api_service"
        pp = "party_party"
        pa = "party_address"
        ppl = "product_price_list"
        ssh = "sale_shop"
        pprod = "product_product"
        pu = "product_uom"
        sm = "stock_move"
        spo = "stock_shipment_out"
        OP_MAP = {"order": "prepaid", "shipment": "picking", "manual": "manual"}
        warehouse_id = self.odoo.search("stock.warehouse", [], limit=1)[0]
        for sale in data:
            if self.d.has_key(getKey(ss, sale["id"])):
                order_data = self.odoo.read(
                    "sale.order",
                    self.d[getKey(ss, sale["id"])],
                    ["state", "procurement_group_id"],
                )
                if order_data:
                    if order_data["state"] == "done":
                        continue
                    elif order_data["state"] == "manual" and sale["state"] == "done":
                        self.odoo.write(
                            "sale.order",
                            self.d[getKey(ss, sale["id"])],
                            {"state": "done"},
                        )
                        continue
                    else:
                        if order_data["procurement_group_id"]:
                            group_id = order_data["procurement_group_id"][0]
                            self.crO.execute(
                                "delete from procurement_order where group_id "
                                "= %s" % group_id
                            )
                            self.crO.execute(
                                "delete from procurement_group where id = %s" % group_id
                            )
                        self.crO.execute(
                            "delete from sale_order_line where "
                            "order_id = %s" % self.d[getKey(ss, sale["id"])]
                        )
                        self.crO.execute(
                            "delete from sale_order where id = %s"
                            % self.d[getKey(ss, sale["id"])]
                        )
                        self.close_crO()
            print "ORIG SALE: ", sale
            payment_term_id = False
            if sale["payment_term"]:
                payment_term_id = self.PAYMENT_TERM_MAP[str(sale["payment_term"])]

            partner_id = self.d[getKey(pp, sale["party"])]
            delivery_address_id = False
            if sale["shipment_address"]:
                delivery_address_id = self.d[getKey(pa, sale["shipment_address"])]

            invoice_address_id = False
            if sale["invoice_address"]:
                invoice_address_id = self.d[getKey(pa, sale["invoice_address"])]

            shop_id = self.d[getKey(ssh, sale["shop"])]
            payment_type_id = False
            if sale["payment_type"]:
                payment_type_id = self.PAYMENT_MODES_MAP[str(sale["payment_type"])]

            carrier_id = False
            if sale["carrier"]:
                carrier_id = self.d[getKey(c, sale["carrier"])]

            price_list_id = 1
            if sale["price_list"]:
                price_list_id = self.d[getKey(ppl, sale["price_list"])]

            carrier_service_id = False
            if sale.get("carrier_service", False):
                carrier_service_id = self.d[getKey(cs, sale["carrier_service"])]

            agent_id = False
            if sale["agent"]:
                agent_id = self.d[getKey(pp, sale["agent"])]

            notes = ""
            if sale["comment"]:
                notes += sale["comment"] + "\n"
            if sale["description"]:
                notes += sale["description"] + "\n"
            if sale.get("esale_coupon", False):
                notes += "CUPON: " + sale["esale_coupon"]

            vals = {
                "name": sale["reference"] or "/",
                "partner_id": partner_id,
                "partner_invoice_id": invoice_address_id or partner_id,
                "partner_shipping_id": delivery_address_id or partner_id,
                "date_order": sale["sale_date"]
                and format_date(sale["sale_date"])
                or format_date(sale["create_date"]),
                "warehouse_id": warehouse_id,
                "pricelist_id": price_list_id,
                "carrier_id": carrier_id,
                "note": notes,
                "picking_policy": "direct",
                "order_policy": OP_MAP[sale["invoice_method"]],
                "payment_term": payment_term_id,
                "payment_mode_id": payment_type_id,
                "carrier_service_id": carrier_service_id,
                "sale_store_id": shop_id,
            }
            if sale.get("reference_external", False):
                vals["client_order_ref"] = sale["reference_external"] or ""
            if sale.get("asm_return", False):
                vals["asm_return"] = sale["asm_return"] or False
            if sale.get("carrier_notes", False):
                vals["carrier_notes"] = sale["carrier_notes"] or ""
            print "vals: ", vals
            order_id = self.odoo.create("sale.order", vals)
            partner_data = self.odoo.read(
                "res.partner", vals["partner_shipping_id"], ["property_stock_customer"]
            )
            customer_loc_id = partner_data["property_stock_customer"][0]
            self.d[getKey(ss, sale["id"])] = order_id

            self.crT.execute(
                "select id,sequence,unit,gross_unit_price,note,"
                "product,description,quantity,discount,"
                "shipment_cost,cost_price,kit_depth,"
                "kit_parent_line from sale_line where sale = %s "
                "order by kit_depth asc" % (sale["id"])
            )
            lines_data = self.crT.fetchall()
            procs = []
            for line in lines_data:
                self.crT.execute(
                    "select tax from sale_line_account_tax where "
                    "line = %s" % (line["id"])
                )
                tax_data = self.crT.fetchall()
                taxes_ids = []
                for tax in tax_data:
                    taxes_ids.extend(self.TAXES_MAP[str(tax["tax"])])

                product_id = False
                if line["product"]:
                    product_id = self.d[getKey(pprod, line["product"])]
                kit_parent_line_id = False
                if line["kit_parent_line"]:
                    kit_parent_line_id = self.d[getKey(sl, line["kit_parent_line"])]
                notes = ""
                if line["note"]:
                    notes = "\n\n" + line["note"]
                uom = 1
                if line["unit"]:
                    uom = self.d[getKey(pu, line["unit"])]
                agents = []
                if agent_id and product_id:
                    commission_ids = self.odoo.search(
                        "product.product.agent",
                        [("product_id", "=", product_id), ("agent", "=", agent_id)],
                    )
                    if commission_ids:
                        commission_data = self.odoo.read(
                            "product.product.agent", commission_ids[0], ["commission"]
                        )
                        agents.append(
                            (
                                0,
                                0,
                                {
                                    "agent": agent_id,
                                    "commission": commission_data["commission"][0],
                                },
                            )
                        )
                    else:
                        commission_ids = self.odoo.search(
                            "product.product.agent",
                            [("product_id", "=", product_id), ("agent", "=", False)],
                        )
                        if commission_ids:
                            commission_data = self.odoo.read(
                                "product.product.agent",
                                commission_ids[0],
                                ["commission"],
                            )
                            agents.append(
                                (
                                    0,
                                    0,
                                    {
                                        "agent": agent_id,
                                        "commission": commission_data["commission"][0],
                                    },
                                )
                            )

                line_vals = {
                    "sequence": line["sequence"] or 0,
                    "price_unit": line["gross_unit_price"]
                    and float(line["gross_unit_price"])
                    or 0.0,
                    "product_id": product_id,
                    "name": line["description"] + notes,
                    "product_uom": uom,
                    "product_uom_qty": line["quantity"]
                    and float(line["quantity"])
                    or 0.0,
                    "discount": line["discount"] and float(line["discount"]) or 0.0,
                    "purchase_price": (
                        line["cost_price"] and float(line["cost_price"]) or 0.0
                    )
                    + (line["shipment_cost"] and float(line["shipment_cost"]) or 0.0),
                    "pack_depth": line["kit_depth"] or 0,
                    "pack_parent_line_id": kit_parent_line_id,
                    "order_id": order_id,
                    "agents": agents,
                    "tax_id": [(6, 0, taxes_ids)],
                }
                print "lines: ", line_vals
                line_id = self.odoo.create(
                    "sale.order.line", line_vals, {"not_expand": True}
                )
                self.d[getKey(sl, line["id"])] = line_id

                self.crT.execute(
                    "select id from stock_move where origin = "
                    "'sale.line,%s'" % (line["id"])
                )
                move_data = self.crT.fetchall()
                for move in move_data:
                    move_id = self.d[getKey(sm, move["id"])]
                    move_info = self.odoo.read(
                        "stock.move", move_id, ["date_expected", "state"]
                    )
                    proc_vals = {
                        "name": line_vals["name"],
                        "origin": vals["name"],
                        "date_planned": move_info["date_expected"],
                        "product_id": product_id,
                        "product_qty": line_vals["product_uom_qty"],
                        "product_uom": line_vals["product_uom"],
                        "invoice_state": vals["order_policy"] == "picking"
                        and "2binvoiced"
                        or "none",
                        "sale_line_id": line_id,
                        "location_id": customer_loc_id,
                        "warehouse_id": warehouse_id,
                        "partner_dest_id": vals["partner_shipping_id"],
                        "state": "confirmed",
                    }
                    print "proc_vals: ", proc_vals
                    proc_id = self.odoo.create("procurement.order", proc_vals)
                    procs.append((proc_id, PROC_MOVE_STATES_MAP[move_info["state"]]))

            if sale["sale_discount"]:
                order_data = self.odoo.read("sale.order", order_id, ["amount_untaxed"])
                discount = order_data["amount_untaxed"] * float(sale["sale_discount"])

                line_vals = {
                    "sequence": 99,
                    "price_unit": -discount,
                    "name": "Descuento global",
                    "product_uom": 1,
                    "product_uom_qty": 1.0,
                    "order_id": order_id,
                }
                self.odoo.create("sale.order.line", line_vals)
                print "Discount line: ", line_vals

            if sale["state"] not in ("draft", "quotation"):
                if sale["state"] == "cancel":
                    self.odoo.exec_workflow("sale.order", "cancel", order_id)
                else:
                    line_ids = self.odoo.search(
                        "sale.order.line", [("order_id", "=", order_id)]
                    )
                    if line_ids:
                        self.odoo.write("sale.order.line", line_ids, {"state": "done"})
                    # No queremos que cree factura
                    reset = False
                    if vals["order_policy"] == "prepaid":
                        self.odoo.write(
                            "sale.order", [order_id], {"order_policy": "picking"}
                        )
                        reset = True

                    self.odoo.exec_workflow("sale.order", "order_confirm", order_id)

                    # Restablecemos
                    if reset:
                        self.odoo.write(
                            "sale.order", [order_id], {"order_policy": "prepaid"}
                        )

                    if not procs:
                        sale_data = self.odoo.read(
                            "sale.order", order_id, ["picking_ids"]
                        )
                        if sale_data["picking_ids"]:
                            move_ids = self.odoo.search(
                                "stock.move",
                                [("picking_id", "in", sale_data["picking_ids"])],
                            )
                            if move_ids:
                                self.odoo.write(
                                    "stock.move", move_ids, {"state": "draft"}
                                )
                                self.odoo.unlink("stock.move", move_ids)
                            self.odoo.unlink("stock.picking", sale_data["picking_ids"])
                            continue

                    sale_data = self.odoo.read(
                        "sale.order", order_id, ["procurement_group_id"]
                    )
                    self.crT.execute(
                        "select id from stock_shipment_out where "
                        "origin_cache = 'sale.sale,%s'" % (sale["id"])
                    )
                    pick_data = self.crT.fetchall()
                    for pick in pick_data:
                        picking_id = self.d[getKey(spo, pick["id"])]
                        self.odoo.write(
                            "stock.picking",
                            picking_id,
                            {
                                "group_id": sale_data["procurement_group_id"]
                                and sale_data["procurement_group_id"][0]
                                or False
                            },
                        )
                    for proc in procs:
                        proc_vals = {
                            "group_id": sale_data["procurement_group_id"]
                            and sale_data["procurement_group_id"][0]
                            or False,
                            "state": proc[1],
                        }
                        self.odoo.write("procurement.order", [proc[0]], proc_vals)
                        print "PROC: ", proc_vals

                    order_data = self.odoo.read("sale.order", order_id, ["state"])
                    if order_data["state"] == "shipping_except":
                        self.odoo.exec_workflow(
                            "sale.order", "ship_corrected", order_id
                        )

        return True

    def migrate_sale_invoice_link(self):
        self.crT.execute(
            "select id,invoice,origin from account_invoice_line "
            "where origin like 'sale.line,%' and invoice is not "
            "null"
        )
        data = self.crT.fetchall()
        ai = "account_invoice"
        ail = "account_invoice_line"
        sol = "sale_line"
        for line in data:
            sale_line_id = int(line["origin"].split(",")[1])
            if self.d.has_key(getKey(sol, sale_line_id)):
                line_id = self.d[getKey(sol, sale_line_id)]
                try:
                    invoice_line_id = self.d[getKey(ail, line["id"])]
                except:
                    continue
                try:
                    invoice_id = self.d[getKey(ai, line["invoice"])]
                except:
                    continue
                self.odoo.write(
                    "sale.order.line",
                    [line_id],
                    {"invoice_lines": [(4, [invoice_line_id])]},
                )
                line_data = self.odoo.read("sale.order.line", line_id, ["order_id"])
                print "SALE: ", line_data["order_id"]
                self.odoo.write(
                    "sale.order",
                    [line_data["order_id"][0]],
                    {"invoice_ids": [(4, [invoice_id])]},
                )
        return True

    def fix_product_migration(self):
        pp = "product_product"
        self.crT.execute(
            "select pp.id, pt.id as template_id from product_product pp inner"
            " join product_template pt on pt.id = pp.template"
        )
        data = self.crT.fetchall()
        list_price_field = cost_price_field = False
        for prod in data:
            vals = {}
            if not cost_price_field:
                self.crT.execute(
                    "select id from ir_model_field where name = "
                    "'cost_price' and module = 'product'"
                )
                field = self.crT.fetchone()
                cost_price_field = field["id"]
            self.crT.execute(
                "select value from ir_property where field = %s "
                "and res = 'product.template,%s' limit 1"
                % (cost_price_field, prod["template_id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                field_value = field_value["value"].replace(",", "")
                vals["standard_price"] = float(field_value)

            if not list_price_field:
                self.crT.execute(
                    "select id from ir_model_field where name = "
                    "'list_price' and module = 'product'"
                )
                field = self.crT.fetchone()
                list_price_field = field["id"]
            self.crT.execute(
                "select value from ir_property where field = %s "
                "and res = 'product.template,%s' limit 1"
                % (list_price_field, prod["template_id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                field_value = field_value["value"].replace(",", "")
                vals["list_price"] = float(field_value)
            print "VALS: ", vals
            self.odoo.write("product.product", self.d[getKey(pp, prod["id"])], vals)

    def fix_product_ean14_migration(self):
        self.crT.execute("select product, number from product_code")
        data = self.crT.fetchall()
        pp = "product_product"
        for product_code in data:
            odoo_product = self.d[getKey(pp, product_code["product"])]
            try:
                self.odoo.write(
                    "product.product", [odoo_product], {"ean13": product_code["number"]}
                )
            except:
                try:
                    self.odoo.write(
                        "product.product",
                        [odoo_product],
                        {"ean14": product_code["number"]},
                    )
                except:
                    pass

    def fix_product_name_migration(self):
        self.crT.execute(
            "select pp.id,name from product_product pp inner"
            " join product_template pt on pt.id = pp.template"
        )
        data = self.crT.fetchall()
        pp = "product_product"
        for product_code in data:
            odoo_product = self.d[getKey(pp, product_code["id"])]
            self.odoo.write(
                "product.product", [odoo_product], {"name": product_code["name"]}
            )

    def fix_party_migration(self):
        aa = "account_account"
        self.crT.execute(
            "select id from ir_model where model = 'party.party' " "limit 1"
        )
        model_id = self.crT.fetchone()
        self.crT.execute(
            "select id from ir_model_field where name = "
            "'account_payable' and module = 'account' and "
            "model = %s limit 1" % model_id["id"]
        )
        payable_field_id = self.crT.fetchone()
        self.crT.execute(
            "select id from ir_model_field where name = "
            "'account_receivable' and module = 'account' and "
            "model = %s limit 1" % model_id["id"]
        )
        receivable_field_id = self.crT.fetchone()

        self.crT.execute("select id from party_party")
        data = self.crT.fetchall()
        for party in data:
            vals = {}
            self.crT.execute(
                "select value from ir_property where field = %s "
                "and res = 'party.party,%s' limit 1"
                % (payable_field_id["id"], party["id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                payable_id = field_value["value"].split(",")[1]
                odoo_payable_id = self.d[getKey(aa, payable_id)]
                vals["property_account_payable"] = odoo_payable_id

            self.crT.execute(
                "select value from ir_property where field = %s "
                "and res = 'party.party,%s' limit 1"
                % (receivable_field_id["id"], party["id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                receivable_id = field_value["value"].split(",")[1]
                odoo_receivable_id = self.d[getKey(aa, receivable_id)]
                vals["property_account_receivable"] = odoo_receivable_id

            odoo_partner_id = self.d[getKey("party_party", party["id"])]
            self.odoo.write("res.partner", odoo_partner_id, vals)

    def fix_lot_migration(self):
        self.crT.execute(
            "select id,life_date,removal_date,expiry_date,"
            "alert_date,lot_date from stock_lot"
        )
        data = self.crT.fetchall()
        sl = "stock_lot"
        for lot in data:
            vals = {
                "create_date": format_date(lot["lot_date"]),
                "life_date": lot["life_date"]
                and format_date(lot["life_date"])
                or False,
                "removal_date": lot["removal_date"]
                and format_date(lot["removal_date"])
                or False,
                "alert_date": lot["alert_date"]
                and format_date(lot["alert_date"])
                or False,
                "use_date": lot["expiry_date"]
                and format_date(lot["expiry_date"])
                or False,
            }
            self.odoo.write("stock.production.lot", self.d[getKey(sl, lot["id"])], vals)
        return True

    def fix_partner_payment_data(self):
        self.crT.execute(
            "select id from ir_model where model = 'party.party' " "limit 1"
        )
        model_id = self.crT.fetchone()
        self.crT.execute(
            "select id from ir_model_field where name = "
            "'lang' and module = 'party' and "
            "model = %s limit 1" % model_id["id"]
        )
        lang_field_id = self.crT.fetchone()
        self.crT.execute(
            "select id from ir_model_field where name = "
            "'customer_tax_rule' and module = 'account' and "
            "model = %s limit 1" % model_id["id"]
        )
        customer_fpos_field_id = self.crT.fetchone()
        self.crT.execute(
            "select id from ir_model_field where name = "
            "'supplier_tax_rule' and module = 'account' and "
            "model = %s limit 1" % model_id["id"]
        )
        supplier_fpos_field_id = self.crT.fetchone()
        self.crT.execute(
            "select id from ir_model_field where name = "
            "'supplier_payment_term' and module = "
            "'account_invoice' and model = %s limit 1" % model_id["id"]
        )
        supplier_pterm_field_id = self.crT.fetchone()
        self.crT.execute(
            "select id from ir_model_field where name = "
            "'customer_payment_term' and module = "
            "'account_invoice' and model = %s limit 1" % model_id["id"]
        )
        customer_pterm_field_id = self.crT.fetchone()
        self.crT.execute(
            "select id from ir_model_field where name = "
            "'sale_price_list' and module = 'sale_price_list' "
            "and model = %s limit 1" % model_id["id"]
        )
        sale_pricelist_field_id = self.crT.fetchone()
        ppl = "product_price_list"

        self.crT.execute("select id from party_party")
        data = self.crT.fetchall()
        for party in data:
            vals = {}
            self.crT.execute(
                "select code from ir_lang where id in "
                "(select split_part(value, ',', 2)::int from "
                "ir_property where res like 'party.party,%s' "
                "and field = %s) limit 1" % (party["id"], lang_field_id["id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                vals["lang"] = field_value["code"]

            self.crT.execute(
                "select value from ir_property where field in "
                "%s and res = 'party.party,%s' and value is not"
                " null limit 1"
                % (
                    (customer_fpos_field_id["id"], supplier_fpos_field_id["id"]),
                    party["id"],
                )
            )
            field_value = self.crT.fetchone()
            if field_value:
                fpos_id = field_value["value"].split(",")[1]
                vals["property_account_position"] = self.FISCAL_POSITIONS_MAP[fpos_id]

            self.crT.execute(
                "select value from ir_property where field = %s "
                "and res = 'party.party,%s' limit 1"
                % (supplier_pterm_field_id["id"], party["id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                pterm_id = field_value["value"].split(",")[1]
                vals["property_supplier_payment_term"] = self.PAYMENT_TERM_MAP[pterm_id]

            self.crT.execute(
                "select value from ir_property where field = %s "
                "and res = 'party.party,%s' limit 1"
                % (customer_pterm_field_id["id"], party["id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                pterm_id = field_value["value"].split(",")[1]
                vals["property_payment_term"] = self.PAYMENT_TERM_MAP[pterm_id]

            self.crT.execute(
                "select value from ir_property where field = %s "
                "and res = 'party.party,%s' limit 1"
                % (sale_pricelist_field_id["id"], party["id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                pricelist_id = int(field_value["value"].split(",")[1])
                if self.d.has_key(getKey(ppl, pricelist_id)):
                    vals["property_product_pricelist"] = self.d[
                        getKey(ppl, pricelist_id)
                    ]

            self.crT.execute(
                "select supplier_payment_type,customer_payment_type "
                "from party_account_payment_type where party = %s "
                "limit 1" % (party["id"])
            )
            field_value = self.crT.fetchone()
            if field_value:
                if field_value["supplier_payment_type"]:
                    pmode_id = str(field_value["supplier_payment_type"])
                    vals["supplier_payment_mode"] = self.PAYMENT_MODES_MAP[pmode_id]
                if field_value["customer_payment_type"]:
                    pmode_id = str(field_value["customer_payment_type"])
                    vals["customer_payment_mode"] = self.PAYMENT_MODES_MAP[pmode_id]

            if vals:
                print "VALS: ", vals
                odoo_partner_id = self.d[getKey("party_party", party["id"])]
                self.odoo.write("res.partner", odoo_partner_id, vals)

    def reimport_medical_code(self):
        self.crT.execute("SELECT id,attributes,manual_code FROM party_party")
        data = self.crT.fetchall()
        pp = "party_party"
        for party_code in data:
            code = ""
            if party_code["attributes"]:
                attribute_dict = eval(party_code["attributes"])
                if "medical_code" in attribute_dict:
                    att_code = attribute_dict["medical_code"]
            if party_code["manual_code"]:
                if code and code != party_code["manual_code"]:
                    print (
                        "diferencia en codigo medico del partner %s" % party_code["id"]
                    )
                if not code:
                    code = party_code["manual_code"]
            if self.d.has_key(getKey(pp, party_code["id"])):
                partner_id = self.d[getKey(pp, party_code["id"])]
                self.odoo.write("res.partner", partner_id, {"medical_code": code})


Tryton2Odoo()
