from config import Config
import commentjson


def tryton2odoo_account_code(account_code):
    return account_code[:4] + account_code[4 - Config.ODOO_ACC_DIGITS:]


def format_date(date):
    return date.strftime("%Y-%m-%d")


def getKey(tryton_model, reg_id):
    return tryton_model + "_" + str(reg_id)


def loadTaxes():
    json_data=open(Config.TAXES_FILE).read()
    return commentjson.loads(json_data)


def loadTaxCodes():
    json_data=open(Config.TAX_CODES_FILE).read()
    return commentjson.loads(json_data)


def loadPaymentModes():
    json_data=open(Config.PAYMENT_MODES_FILE).read()
    return commentjson.loads(json_data)


def loadProductUoms():
    json_data=open(Config.PRODUCT_UOM_FILE).read()
    return commentjson.loads(json_data)
