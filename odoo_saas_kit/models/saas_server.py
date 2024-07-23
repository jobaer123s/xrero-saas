# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.modules.module import get_module_resource
from . lib import check_connectivity
from . lib import check_if_db_accessible
import logging
# _logger = logging.Logger(__name__)
_logger = logging.getLogger(__name__)


SERVER_TYPE = [
    ('containerized', "Containerized Instance"),
    # ('same_odoo_server', "Current Odoo Server"),
    # ('different_odoo_server', "Same machine with different odoo server"),
    # ('different_odoo_server', "Different Odoo Server"),
]
DB_SCHEME = [
    ('create', "Database creation"),
    ('clone', "Database cloning"),
]
HOST_SERVER = [
    ('self', "Self (Same Server)"),
    ('remote', "Remote Server"),
]
DB_SERVER = [
    ('self', "Self (Same Server)"),
    ('remote', "Remote Server"),
]
STATE = [
    ('draft', "Draft"),
    ('validated', 'Validated'),
    ('confirm', "Confirm"),
]


class SaasServer(models.Model):
    _name = "saas.server"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Class for managing server types for deploying SaaS architecture.'

    def _compute_total_clients(self):
        for server in self:
            number_of_clients = len(
                self.env['saas.client'].sudo().search(
                    [('server_id', '=', server.id), ('state', '!=', 'cancel')]))
            server.total_clients = number_of_clients

    name = fields.Char(string="Plan", required=True,help="Name for the server")
    server_type = fields.Selection(
        selection=SERVER_TYPE,
        string="Type",
        required=True,
        default="containerized",
        readonly=True)
    host_server = fields.Selection(
        selection=HOST_SERVER,
        string="Host Server",
        required=True,
        default="self")
    db_server = fields.Selection(
        selection=DB_SERVER,
        string="Database Host Server",
        required=True,
        default="self")
    max_clients = fields.Integer(
        string="Maximum Allowed Clients",
        default="10",
        required=True,
        help="Maximum odoo instance that can run on this server")
    is_host_validated = fields.Boolean(string="Is Host Validated", default=False)
    is_db_validated = fields.Boolean(string="Is DB Validated", default=False)
    server_domain = fields.Char(string="Server Domain(Default)", required=True)
    odoo_url = fields.Char(string="Odoo URL")
    db_host = fields.Char(string="Database Host", default="localhost")
    db_port = fields.Char(string="Database Port", default="5432")
    db_user = fields.Char(string="Database Username",help="Username of the Database")
    db_pass = fields.Char(string="Database Password",help="Password of the Database")
    sftp_host = fields.Char(string="SFTP Host")
    sftp_port = fields.Char(
        string="SFTP Port",
        default="22")
    sftp_user = fields.Char(string="User")
    sftp_password = fields.Char(string="Password")
    db_creation_scheme = fields.Selection(
        selection=DB_SCHEME,
        string="Database Scheme",
        default="create")
    base_db = fields.Char(string="Base Database Name")
    sequence = fields.Integer(
        'sequence',
        help="Sequence for the handle.",
        default=10)
    total_clients = fields.Integer(
        compute='_compute_total_clients',
        string="No. Of Clients", tracking=True)
    state = fields.Selection(selection=STATE, string="State", default="draft", tracking=True)
    module_installation_limit = fields.Integer(string="Module installation limit", default=5)
    active = fields.Boolean(string="Active", default=True,  tracking=True)

    def print_logs(self, log_type, message, line_no):
        if log_type=='info':
            _logger.info("Saas Server SERVER{} : {} at Line {}".format(self.id, message, line_no))
        elif log_type=='warn':
            _logger.info("Warning in Saas Server SERVER{} : {} at Line {}".format(self.id, message, line_no))
        elif log_type=='error':
            _logger.info("Error in Saas Server SERVER{} : {} at Line {}".format(self.id, message, line_no))


    def test_host_connection(self):
        """ 
        Method to check Host connection: called by the button 'Test Connection'
        """
        
        for obj in self:
            response = obj.check_host_connected_call()
            if response.get('status'):
                obj.is_host_validated = True
                if obj.is_db_validated:
                    obj.state = 'validated'
                obj._cr.commit()
                # raise UserError("Connection successful!")
                message = self.env['custom.message.wizard'].create({'message':"Connection successful!"})
                action = self.env.ref('odoo_saas_kit.custom_message_wizard_action').read()[0]
                action['res_id'] = message.id
                return action
            else:
                raise UserError(response.get('message'))
                
    
    def check_host_connected_call(self):
        """
            Method to call the script to check host connectivity, 
            return response dict as per the output.
            Called from 'test_host_connection' and  'set_validated'
        """
        self.print_logs('info', 'Called check_host_connected_call', '135')

        response = dict(
            status=True,
            message='Success'
        )
        host_server, _ = self.get_server_details()
        try:
            self.print_logs('info', 'calling check_connectivity script', '143')
            response = check_connectivity.ishostaccessible(host_server)
        except Exception as e:
            self.print_logs('error', e, '146')
            response['status'] = False
            response['message'] = e      
        return response

    def test_db_connection(self, from_set=False):
        """ 
        Method to check DB connection: called by the button 'Test Connection'
        """
                
        for obj in self:
            response = obj.check_db_connection_call()
            if response.get('status'):
                obj.is_db_validated = True
                if obj.state == 'draft':
                    if obj.host_server == 'remote':
                        if obj.is_host_validated:
                            obj.state = 'validated'
                    else:
                        obj.state = 'validated'
                obj._cr.commit()
                # raise UserError("Connection successful!")
                message = self.env['custom.message.wizard'].create({'message':"Connection successful!"})
                action = self.env.ref('odoo_saas_kit.custom_message_wizard_action').read()[0]
                action['res_id'] = message.id
                return action
            else:
                raise UserError(response.get('message'))
        
    def check_db_connection_call(self):
        """
            Method to call the script to check DB connectivity, 
            return response dict as per the output.
            Called from 'test_db_connection' and  'set_validated'
        """
        self.print_logs('info', 'called check_db_connection_call', '177')
        response = dict(
            status=True,
            message='Success'
        )
        try:
            _, db_server = self.get_server_details()
            config_path = get_module_resource('odoo_saas_kit')
            self.print_logs('info', 'calling check_if_db_accessible script', '185')
            response = check_if_db_accessible.isdbaccessible(host_server = _ , db_server = db_server, config_path=config_path)                
        except Exception as e:
            self.print_logs('error', e, '188')
            response['status'] = False
            response['message'] = e      
        return response

    def set_validated(self):
        """
        Method called by the button 'validate'.
        It call both the check_db_connection_call and _host check_host_connected_call, and change the state if both the connection successful.
        """
        
        for obj in self:
            obj.check_db_connection_call()
            if obj.host_server == 'remote':
                obj.check_host_connected_call()
    
    def set_confirm(self):
        """
            Confirm the state of Server,
            Called from Button on Server page
        """
        
        for obj in self:
            obj.state = 'confirm'

    def reset_to_draft(self):
        """
            Method to change the state of Server to make any changes in it.
            Called from Reset To Draft button available over server record
        """
        
        for obj in self:
            plans = self.env['saas.plan'].search([('server_id', '=', obj.id), ('state', '=', 'confirm')])
            if plans:
                raise UserError("This Server has some confirmed SaaS Plan(s)!")
            obj.state = 'draft'


    def write(self, vals):
        for obj in self:
            if vals.get('active')==False:
                if obj.state != 'draft':
                    raise UserError("You cannot archive a validated or confirmed SaaS server.")
        return super(SaasServer, self).write(vals)
    

    def unlink(self):
        """
            Delete the server if only No plan is associated with the server
        """
        
        for obj in self:
            if obj.state == 'confirm':
                raise UserError("You must reset the SaaS Server to draft first!")
            plans = self.env['saas.plan'].search([('server_id', '=', obj.id), ('state', '=', 'confirm')])
            if plans:
                raise UserError("You must delete the associated SaaS Plan(s) first!")
        return super(SaasServer, self).unlink()

    @api.model
    def get_server_details(self):
        """
            Method created to return value host and db server as dict,
            Called from various methods in the complete process
        """
        self.print_logs('info', 'Called get_server_details', '239')

        host_server = dict(
            server_type=self.host_server,
            host=self.sftp_host,
            port=self.sftp_port,
            user=self.sftp_user,
            password=self.sftp_password,
            server_domain = self.server_domain
        )
        db_server = dict(
            server_type=self.db_server,
            host= self.db_host,
            port= self.db_port or 5432,
            user=self.db_user,
            password=self.db_pass
        )
        self.print_logs('info', 'return get_server_details response', '256')
        return host_server, db_server

class SaasMultiServer(models.Model):
    _name = 'server.priority'
    _description = "Server Priority"

    name = fields.Char()
    server_id = fields.Many2one(comodel_name='saas.server', string="Server", domain="[('state', '=', 'confirm')]")
    priority = fields.Integer(string="Priority", default=1)
    saas_plan_id = fields.Many2one(comodel_name='saas.plan')
