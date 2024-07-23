# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from urllib.parse import urlparse
from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError
from odoo.modules.module import get_module_resource
from odoo.models import NewId
from datetime import datetime
import string
import random
import logging
import base64
from . lib import saas
from . lib import query
from . lib import containers
from . lib import client

_logger = logging.getLogger(__name__)

MODULE_STATUS = [
    ('installed', "Installed"),
    ('uninstalled', "Not Installed")]

CLIENT_STATE = [
    ('draft', "Draft"),
    ('started', "Started"),
    ('stopped', "Stopped"),
    ('inactive', 'Inactive'),
    ('cancel', 'Cancel'),]

def _code_generator(size=5, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class SaasClient(models.Model):
    _name = 'saas.client'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Class for managing SaaS Instances(Clients)'

    @api.depends('data_directory_path')
    def _compute_addons_path(self):
        for obj in self:
            if obj.data_directory_path and type(obj.id) != NewId:
                obj.addons_path = "{}/addons/17.0".format(
                    obj.data_directory_path)
            else:
                obj.addons_path = ""

    name = fields.Char(string="Name",help="Name of Client. Unique and auto generated")
    client_url = fields.Char(string="URL",help="Url for the client's Odoo Instance")
    database_name = fields.Char(string="Database Name",help="Client's Database Name")
    saas_contract_id = fields.Many2one(comodel_name="saas.contract", string="SaaS Contract",help="Id of the related Saas Contract")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Customer",help="Id of the customer/client/user in the main odoo Instance")
    containter_port = fields.Char(string="Port",help="PORT on which client's container is runing ")
    containter_path = fields.Char(string="Path",help="Path of the client's container")
    container_name = fields.Char(string="Instance Name",help="Name of the client's container")
    container_id = fields.Char(string="Instance ID")
    data_directory_path = fields.Char(string="Data Directory Path")
    addons_path = fields.Char(compute='_compute_addons_path', string="Extra Addons Path",help="Path of the addons module")
    saas_module_ids = fields.One2many(comodel_name="saas.module.status", inverse_name="client_id", string="Related Modules",help="List of the modules installed in the client's Odoo Instance")
    server_id = fields.Many2one(comodel_name="saas.server", string="SaaS Server",help="Id of the server on which the Client's container is running")
    invitation_url = fields.Char("Invitation URL")
    state = fields.Selection(selection=CLIENT_STATE, default="draft", string="State", tracking = True)
    is_drop_db = fields.Boolean(string="Drop Db", default=False)
    is_drop_container = fields.Boolean(string="Drop Container", default=False)

    active = fields.Boolean(string="Active", default=True)
    login_with_custom_domain = fields.Boolean("Login with Custom Domain", default=False)
    has_custom_domain = fields.Boolean("Has Custom Domain", compute="_compute_has_custom_domain")

    _sql_constraints = [
        ('database_name_uniq', 'unique(database_name)', 'Database Name Must Be Unique !!!'),
    ]



    @api.depends('saas_contract_id')
    def _compute_has_custom_domain(self):
        for rec in self:
            if rec.saas_contract_id and rec.saas_contract_id.custom_domain_ids and rec.saas_contract_id.custom_domain_ids.filtered(lambda d: d.status=='active'):
                rec.has_custom_domain = True
            else:
                rec.has_custom_domain = False
    
    
    def print_logs(self, log_type, message, line_no):
        if log_type=='info':
            _logger.info("Saas Cleint CLIENT{} : {} at Line {}".format(self.id, message, line_no))
        elif log_type=='warn':
            _logger.info("Warning in Saas Cleint CLIENT{} : {} at Line {}".format(self.id, message, line_no))
        elif log_type=='error':
            _logger.info("Error in Saas Cleint CLIENT{} : {} at Line {}".format(self.id, message, line_no))

    @api.model
    def create_docker_instance(self, domain_name=None):
        modules = [module.technical_name for module in self.saas_module_ids]
        host_server, db_server = self.saas_contract_id.server_id.get_server_details()
        response = None
        self.database_name = domain_name.replace("https://", "").replace("http://", "")
        config_path = get_module_resource('odoo_saas_kit')
        self.print_logs('info', 'calling saas script to create client instance', '93')
        response = saas.main(dict(
            db_template = self.saas_contract_id.db_template,
            db_name=self.database_name,
            modules=modules,
            config_path = config_path,
            host_domain=domain_name,
            host_server=host_server,
            db_server=db_server)
        )
        return response

    @api.model
    def create_client_instance(self, domain_name=None):
        server_id = self.server_id
        if server_id.server_type == 'containerized':
            return self.create_docker_instance(domain_name)
        return False

    def fetch_client_url(self, domain_name=None):
        for obj in self:
            if type(domain_name) != str:
                if obj.saas_contract_id.use_separate_domain:
                    domain_name = obj.saas_contract_id.domain_name
                else:
                    domain_name = "{}.{}".format(obj.saas_contract_id.domain_name, obj.saas_contract_id.saas_domain_url)

            response = None
            try:
                response = obj.create_client_instance(domain_name)
            except Exception as e:
                raise UserError("Unable To Create Client\nERROR: {}".format(e))
            if response:
                obj.client_url = response.get("url", False)
                obj.containter_port = response.get("port", False)
                obj.containter_path = response.get("path", False)
                obj.container_name = response.get("name", False)
                obj.container_id = response.get("container_id", False)
                obj.state = "started"
                obj.saas_contract_id.under_process = False

                obj.data_directory_path = response.get("extra-addons", False)
                if response.get("modules_installation", False):
                    for module_status_id in obj.saas_module_ids:
                        module_status_id.status = 'installed'
                else:
                    for module_status_id in obj.saas_module_ids:
                        if module_status_id.technical_name not in response.get("modules_missed", []):
                            module_status_id.status = 'installed'
            else:
                raise UserError("Couldn't create the instance with the selected domain name. Please use some other domain name.")

    def login_to_client_instance(self):
        for obj in self:
            host_server, db_server = obj.saas_contract_id.server_id.get_server_details()
            self.print_logs('info', 'calling query script', 162)
            response = query.get_credentials(
                obj.database_name,
                host_server=host_server,
                db_server=db_server)
            if response.get('status'):
                response = response.get('result')
                login = response[0][0]
                password = response[0][1]
                login_url = None
                if not obj.login_with_custom_domain:
                    login_url = "{}/saas/login?db={}&login={}&passwd={}".format(obj.client_url, obj.database_name, login, password)
                else:
                    active_domains = obj.saas_contract_id.custom_domain_ids and obj.saas_contract_id.custom_domain_ids.filtered(lambda r: r.status == "active")
                    custom_domain = active_domains[-1] if active_domains else None
                    _logger.info("======== active_domains ====== %r", active_domains)
                    if custom_domain:
                        login_url = "http://{}/saas/login?db={}&login={}&passwd={}".format(custom_domain.name, obj.database_name, login, password)
                        _logger.info("========== login url =========== %r", login_url)
                    else:
                        login_url = "{}/saas/login?db={}&login={}&passwd={}".format(obj.client_url, obj.database_name, login, password)
                        # raise UserError("Custom domain doesn't exist for this instance. Please create a custom domain first and try again.")
                    
                return {
                    'type': 'ir.actions.act_url',
                    'url': login_url,
                    'target': 'new',
                }
            else:
                self.print_logs('error', response.get('message'), 162)
                raise UserError(response.get('message'))

    def stop_client(self):
        for obj in self:
            host_server, db_server = obj.saas_contract_id.server_id.get_server_details()
            response_flag = containers.action(operation="stop",container_id=obj.container_id,host_server = host_server,db_server = db_server)
            if response_flag:
                obj.state = "stopped"
            else:
                raise UserError("Operation Failed! Unknown Error!")

    def start_client(self):
        for obj in self:
            if obj.saas_contract_id.state == 'hold':
                raise UserError("Related Contract is on Hold Please resume the contract first !")
            host_server, db_server = obj.saas_contract_id.server_id.get_server_details()
            response_flag = containers.action(operation="start",container_id=obj.container_id,host_server=host_server,db_server= db_server )
            if response_flag:
                obj.state = "started"
            else:
                raise UserError("Operation Failed! Unknown Error!")

    def restart_client(self):
        for obj in self:
            host_server, db_server = obj.saas_contract_id.server_id.get_server_details()
            response_flag = containers.action(operation="restart",container_id=obj.container_id,host_server=host_server,db_server= db_server )
            if response_flag:
                obj.state = "started"
            else:
                raise UserError("Operation Failed! Unknown Error!")

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('saas.client')
        return super(SaasClient, self).create(vals)

    def write(self, vals):
        initial_list = self.saas_module_ids
        initial_module_name_list =[]
        for rec in initial_list:
            initial_module_name_list.append(rec.module_id.name)
        if vals.get('active')==False:
            if self.state != 'cancel':
                raise UserError("Please cancel the active client before archiving it.")
        result =  super(SaasClient, self).write(vals)
        final_list = self.saas_module_ids
        final_module_name_list =[]
        for rec in final_list:
            final_module_name_list.append(rec.module_id.name)
        if len(final_module_name_list)>len(initial_module_name_list):
            self.message_post(body="The "+str(set(final_module_name_list) - set(initial_module_name_list))+ ' has been added')
        
        if len(final_module_name_list)<len(initial_module_name_list):
            self.message_post(body="The "+str(set(initial_module_name_list) - set(final_module_name_list))+ ' has been removed')
        
        return result

    def inactive_client(self):
        for obj in self:
            if obj.state in ['stopped', 'draft']:
                obj.state = 'inactive'
            else:
                raise UserError("Can't Inactive a Running Client") 

    def unlink(self):
       for obj in self:
          if obj.state == 'cancel':
              res = super(SaasClient, obj).unlink()
          else:
              raise UserError("Can't Delete Instances")
       return res

    def drop_db(self):
        for obj in self:
            try:
                if obj.state == "inactive":
                    host_server, db_server = obj.saas_contract_id.server_id.get_server_details()
                    _logger.info("HOST SERER %r   DB SERVER  %r"%(host_server,db_server))
                    self.print_logs('info', 'calling client.main script', 216)
                    response = client.main(obj.database_name, obj.containter_port, host_server, get_module_resource('odoo_saas_kit'), from_drop_db=True)
                    if not response['db_drop']:
                        raise UserError("ERROR: Couldn't Drop Client Database. Please Try Again Later.\n\nOperation\tStatus\n\nDrop database: \t{}\n".format(response['db_drop']))
                    else:
                        obj.is_drop_db = True
                        if obj.is_drop_container:
                            obj.saas_contract_id.state = 'cancel'
                            obj.state = 'cancel'
            except Exception as e:
                raise UserError(e)

    def drop_container(self):
        for obj in self:
            if obj.state == "inactive" and obj.container_id:
                host_server, db_server = obj.saas_contract_id.server_id.get_server_details()
                _logger.info("HOST SERER %r   DB SERVER  %r"%(host_server,db_server))
                self.print_logs('info', 'calling client.main script', 231)
                try:
                    response = client.main(obj.database_name, obj.containter_port, host_server, get_module_resource('odoo_saas_kit'), container_id=obj.container_id, db_server=db_server, from_drop_container=True)
                    if not response['drop_container'] or not response['delete_nginx_vhost'] or not response['delete_data_dir']:
                        raise UserError("ERROR: Couldn't Drop Client Container. Please Try Again Later.\n\nOperation\tStatus\n\nDelete Domain Mapping: \t{}\nDelete Data Directory: \t{}".format(response['drop_container'], response['delete_nginx_vhost']))
                    else:
                        obj.is_drop_container = True
                        if obj.is_drop_db:
                            obj.saas_contract_id.state = 'cancel'
                            obj.state = 'cancel'
                except Exception as e:
                    raise UserError(f"{e}")
            else:
                obj.is_drop_container = True
                if obj.is_drop_db:
                    obj.saas_contract_id.state = 'cancel'
                    obj.state = 'cancel'

    def cancel_client(self):
        for obj in self:
            if obj.state == 'inactive':
                if not obj.is_drop_db:
                    raise UserError("Please Drop DB to cancel the client.")
                if not obj.is_drop_container:
                    raise UserError("Please Drop Container to cancel the client.")
                else:
                    obj.state = 'cancel'
            elif obj.state == 'draft':
                obj.state='cancel'                
            else:
                raise UserError('Please Inactive the Client first to cancel !')
