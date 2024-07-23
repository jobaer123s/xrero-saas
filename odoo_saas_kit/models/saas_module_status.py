# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import fields, models, api
from odoo.exceptions import UserError,  ValidationError
from . lib import saas_client_db
from . lib import query
import logging

_logger = logging.getLogger(__name__)

MODULE_STATUS = [('installed', "Installed"), 
                ('uninstalled', "Not Installed")]

class ModuleStatus(models.Model):
    _name = 'saas.module.status'
    _description = 'Class for managing module instalation status in client record.'

    module_id = fields.Many2one(comodel_name="saas.module", string="Module")
    technical_name = fields.Char(string="Technical Name", related="module_id.technical_name", readonly=True)
    status = fields.Selection(selection=MODULE_STATUS, default="uninstalled")
    client_id = fields.Many2one(comodel_name="saas.client", string="SaaS Client")
    plan_id = fields.Many2one(comodel_name="saas.plan", string="SaaS Plan")

    def install_module(self):
        for obj in self:
            login=None
            password=None
            host_server, db_server = obj.client_id.server_id.get_server_details()
            response = query.get_credentials(
                obj.client_id.database_name,
                host_server=host_server,
                db_server=db_server)

            if response.get('status'):
                response = response.get('result')
                login = response[0][0]
                password = response[0][1]
            else:
                raise UserError("ERR001: "+str(response.get('message')))
            
            endpoint = str(host_server.get('host')) if (host_server['server_type'] == 'remote') else "localhost"
            saas_port = obj.client_id.containter_port

            data = dict(
                operation="install",
                #odoo_url=obj.client_id.client_url,
                odoo_url="http://{}:{}".format(endpoint, saas_port),
                odoo_username=login,
                odoo_password=password,
                database_name=obj.client_id.database_name,
                modules_list=[obj.technical_name],
            )
            response = saas_client_db.create_saas_client(**data)
            if not response.get("modules_installation", False):
                missed_list = ", ".join(response.get('modules_missed'))
                raise UserError("Could't Install the following modules:\n{}".format(missed_list))
            else:
                obj.status = "installed"

    def uninstall_module(self):
        pass

    def upgrade_module(self):
        pass
