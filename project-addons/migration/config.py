class Config(object):
    TRYTON_ACC_DIGITS = 9
    ODOO_ACC_DIGITS = 8

    ODOO_XMLRPC_PORT = 8069
    ODOO_XMLRPC_URL = "http://%s:%s/xmlrpc/%s"
    ODOO_XMLRPC_HOST = "localhost"
    ODOO_USER = "admin"
    ODOO_PASSWD = "admin"

    ODOO_DATABASE = "besthetic_devel"
    TRYTON_DATABSE = "besthetic_tryton"
    ODOO_DB_USER = "oerp"
    ODOO_DB_PASSWORD = "oerp"
    ODOO_DB_HOST = "localhost"
    TRYTON_DB_USER = "oerp"
    TRYTON_DB_PASSWORD = "oerp"
    TRYTON_DB_HOST = "localhost"

    TAXES_FILE = "data/bstt_map_taxes.json"
    TAX_CODES_FILE = "data/bstt_map_tax_codes.json"
