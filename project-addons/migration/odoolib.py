from config import Config
import xmlrpclib
import socket


class OdooConnect(object):
    def __init__(self):
        login_facade = xmlrpclib.ServerProxy(
            Config.ODOO_XMLRPC_URL
            % (Config.ODOO_XMLRPC_HOST, Config.ODOO_XMLRPC_PORT, "common")
        )
        self.user_id = login_facade.login(
            Config.ODOO_DATABASE, Config.ODOO_USER, Config.ODOO_PASSWD
        )
        self.object_facade = xmlrpclib.ServerProxy(
            Config.ODOO_XMLRPC_URL
            % (Config.ODOO_XMLRPC_HOST, Config.ODOO_XMLRPC_PORT, "object")
        )

    def create(self, model, data, context={}):
        """
        Wrapper of method create
        """
        try:
            res = self.object_facade.execute(
                Config.ODOO_DATABASE,
                self.user_id,
                Config.ODOO_PASSWD,
                model,
                "create",
                data,
                context,
            )
            return res
        except socket.error, err:
            raise Exception("Connection rejected: %s!" % err)
        except xmlrpclib.Fault, err:
            raise Exception("Error %s in create: %s" % (err.faultCode, err.faultString))

    def search(
        self,
        model,
        query,
        offset=0,
        limit=False,
        order=False,
        context={},
        count=False,
        obj=1,
    ):
        """
        Wrapper of method search.
        """
        try:
            ids = self.object_facade.execute(
                Config.ODOO_DATABASE,
                self.user_id,
                Config.ODOO_PASSWD,
                model,
                "search",
                query,
                offset,
                limit,
                order,
                context,
                count,
            )
            return ids
        except socket.error, err:
            raise Exception("Connection rejected: %s!" % err)
        except xmlrpclib.Fault, err:
            raise Exception("Error %s in search: %s" % (err.faultCode, err.faultString))

    def read(self, model, ids, fields, context={}):
        """
        Wrapper of method read.
        """
        try:
            data = self.object_facade.execute(
                Config.ODOO_DATABASE,
                self.user_id,
                Config.ODOO_PASSWD,
                model,
                "read",
                ids,
                fields,
                context,
            )
            return data
        except socket.error, err:
            raise Exception("Connection rejected: %s!" % err)
        except xmlrpclib.Fault, err:
            raise Exception("Error %s in read: %s" % (err.faultCode, err.faultString))

    def write(self, model, ids, field_values, context={}):
        """
        Wrapper of method write.
        """
        try:
            res = self.object_facade.execute(
                Config.ODOO_DATABASE,
                self.user_id,
                Config.ODOO_PASSWD,
                model,
                "write",
                ids,
                field_values,
                context,
            )
            return res
        except socket.error, err:
            raise Exception("Connection rejected: %s!" % err)
        except xmlrpclib.Fault, err:
            raise Exception("Error %s in write: %s" % (err.faultCode, err.faultString))

    def unlink(self, model, ids, context={}):
        """
        Wrapper of method unlink.
        """
        try:
            res = self.object_facade.execute(
                Config.ODOO_DATABASE,
                self.user_id,
                Config.ODOO_PASSWD,
                model,
                "unlink",
                ids,
                context,
            )
            return res
        except socket.error, err:
            raise Exception("Connection rejected: %s!" % err)
        except xmlrpclib.Fault, err:
            raise Exception("Error %s in unlink: %s" % (err.faultCode, err.faultString))

    def default_get(self, model, fields_list=[], context={}):
        """
        Wrapper of method default_get.
        """
        try:
            res = self.object_facade.execute(
                Config.ODOO_DATABASE,
                self.user_id,
                Config.ODOO_PASSWD,
                model,
                "default_get",
                fields_list,
                context,
            )
            return res
        except socket.error, err:
            raise Exception("Connection rejected: %s!" % err)
        except xmlrpclib.Fault, err:
            raise Exception(
                "Error %s in default_get: %s" % (err.faultCode, err.faultString)
            )

    def execute(self, model, method, *args, **kw):
        """
        Wrapper of method execute.
        """
        try:
            res = self.object_facade.execute(
                Config.ODOO_DATABASE,
                self.user_id,
                Config.ODOO_PASSWD,
                model,
                method,
                *args,
                **kw
            )
            return res
        except socket.error, err:
            raise Exception("Connection rejected: %s!" % err)
        except xmlrpclib.Fault, err:
            raise Exception(
                "Error %s in execute: %s" % (err.faultCode, err.faultString)
            )

    def exec_workflow(self, model, signal, ids):
        """Executes a workflow by xmlrpc"""
        try:
            res = self.object_facade.exec_workflow(
                Config.ODOO_DATABASE,
                self.user_id,
                Config.ODOO_PASSWD,
                model,
                signal,
                ids,
            )
            return res
        except socket.error, err:
            raise Exception("Connection rejected: %s!" % err)
        except xmlrpclib.Fault, err:
            raise Exception(
                "Error %s in exec_workflow: %s" % (err.faultCode, err.faultString)
            )
