# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.models import NewId
from odoo.modules.module import get_module_resource
from odoo.addons.odoo_saas_kit.models.lib import saas
from odoo.addons.odoo_saas_kit.models.lib import query
from odoo.addons.odoo_saas_kit.models.lib import client

import logging


_logger = logging.getLogger(__name__)

STATE = [
    ('open', 'Open'),
    ('confirm', 'Confirm'),
    ('cancel', 'Cancel')
]

class SaasOdooVersion(models.Model):
    _name = 'saas.odoo.version'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string="Version Name")
    code = fields.Char(string="Version Code")
    state = fields.Selection(selection=STATE, string="State", default="open",tracking = True)
    is_template_created = fields.Boolean(string="Template Created", default=False)
    db_template = fields.Char(string="DB Template", compute="_compute_db_template_name", store=True)
    product_id = fields.Many2one(comodel_name="product.product", string="Template Product", domain="[('is_saas_module', '=', True)]")
    use_specific_user_template = fields.Boolean(
        string="Use Specific User Template", help="""Select if you want to provide some specific permissions to your user for acessing its odoo instance which is going to be created by this plan.""",tracking = True)
    template_user_id = fields.Char(string="Database Template User ID", help="""Enter the user_id of User which you have created in the DB Template with some specific permissions or whose permission you want to grant to the user of odoo instances which is going to be created by this plan.""")
    is_multi_server = fields.Boolean(string="Deploy Client's on Remote Server", default=False)
    default_saas_servers_ids = fields.One2many(comodel_name="server.priority", inverse_name="saas_version_id")
    is_drop_db = fields.Boolean(string="Is DB Dropped", default=False)

    def create_db_template(self):
        for obj in self:
            server_id = self.env['saas.server'].sudo().search([('state', '=', 'confirm')], limit=1)
            if not server_id:
                raise UserError("Please confirm Atleast One server to Continue")
            if not obj.db_template:
                raise UserError("Please select the DB template name first.")
            config_path = get_module_resource('odoo_saas_kit')
            db_template_name = "template_{}".format(obj.db_template)
            modules = ['wk_saas_tool']
            host_server, db_server = server_id.get_server_details()
            try:
                response = saas.create_db_template(
                    db_template=db_template_name,
                    modules=modules,
                    config_path=config_path,
                    host_server=host_server,
                    db_server=db_server,
                    version=obj.code)
            except Exception as e:
                raise UserError(e)
            else:
                if response:
                    if response.get('status', False):
                        obj.db_template = db_template_name
                        obj.state = 'confirm'
                    else:
                        msg = response.get('msg', False)
                        if msg:
                            raise UserError(msg)
                        else:
                            raise UserError("Unknown Error. Please try again later with some different Template Name")
                else:
                    raise UserError("No Response. Please try again later with some different Template Name")

    def unlink(self):
        for obj in self:
            contracts = self.env['saas.contract'].sudo().search([('odoo_version_id', '=', obj.id), ('state', '!=', 'cancel')])
            if len(contracts):
                raise UserError("There are few contracts which are linked with this version and they are not cancel. Please cancel them first to delete this record.")
            elif obj.state=='confirm':
                raise UserError("You cannot delete the confirmed saas odoo version.")
            else:
                return super(SaasOdooVersion, self).unlink()
            
    def cancel_odoo_version(self):
        for obj in self:
            contracts = self.env['saas.contract'].sudo().search([('odoo_version_id', '=', obj.id), ('state', '!=', 'cancel')])
            if contracts:
                raise UserError("Please Cancel the Linked Contract first before cancel the saas odoo version.")
            else:
                action = self.env.ref('saas_kit_custom_plans.action_cancel_odoo_version_wizard').read()[0]
                return action


    def login_to_template(self):
        for obj in self:
            server_id = self.env['saas.server'].sudo().search([('host_server', '=', 'self'), ('state', '=', 'confirm')], limit=1)
            if not server_id:
                raise UserError("Please configure atleast one self server to continue..")
            host_server, db_server = server_id.get_server_details()
            response = query.get_credentials(
                obj.db_template,
                host_server=host_server,
                db_server=db_server)
            if response.get('status'):
                response = response.get('result')
                login = response[0][0]
                password = response[0][1]
                login_url = "http://db{}_templates.{}/saas/login?db={}&login={}&passwd={}".format(obj.code.split('.')[0],server_id.server_domain,obj.db_template, login, password)
                _logger.info("$$$$$$$$$$$$$$%r", login_url)
                return {
                    'type': 'ir.actions.act_url',
                    'url': login_url,
                    'target': 'new',
                }
            else:
                raise UserError(response.get('message'))
            


    @api.depends('name')
    def _compute_db_template_name(self):
        for obj in self:
            if obj.name and type(obj.id) != NewId and not obj.db_template:
                template_name = obj.name.lower().replace(" ", "_")
                obj.db_template = "{}_tid_{}".format(template_name, obj.id)

    @api.model
    def get_default_saas_values(self):
        data = dict()
        IrDefault = self.env['ir.default'].sudo()
        data['is_odoo_version'] = IrDefault._get('res.config.settings', 'is_odoo_version')
        data['odoo_version'] = self.env['saas.odoo.version'].sudo().search([('state', '=', 'confirm')]) if data['is_odoo_version'] else self.env['saas.odoo.version'].sudo().search([('state', '=', 'confirm'), ('code', '=', '17.0')], limit=1)
        data['is_users'] = IrDefault._get('res.config.settings', 'is_users')
        data['apps_view'] = IrDefault._get('res.config.settings', 'apps_view')
        data['is_free_users'] = IrDefault._get('res.config.settings', 'is_free_users')
        data['free_users'] = int(IrDefault._get('res.config.settings', 'free_users') or 0) if data['is_free_users'] else 0
        data['is_free_users'] = data['is_free_users'] if data['free_users'] else False
        data['addons_path'] = IrDefault._get('res.config.settings', 'addons_path')
        data['max_users'] = IrDefault._get('res.config.settings', 'max_users')
        data['is_multi_server'] = self.is_multi_server
        data['user_cost'] = int(IrDefault._get('res.config.settings', 'user_cost') or 0)
        data['annual_discount'] = IrDefault._get('res.config.settings', 'annual_discount'),
        data['discount_percent'] = float(IrDefault._get('res.config.settings', 'discount_percent') or 0.00)
        
        return data
    
    @api.constrains('default_saas_servers_ids')
    def _check_saas_server_priority(self):
        if any(len(plan.default_saas_servers_ids) != len(plan.default_saas_servers_ids.mapped('server_id')) for plan in self):
            raise UserError(('You cannot define two Priorities lines for the same Server.'))
        
        for obj in self:
            if obj.is_multi_server and len(obj.default_saas_servers_ids.mapped('priority')) != len(set(obj.default_saas_servers_ids.mapped('priority'))):
                raise UserError("Two servers cannot have same priority, Please udpate priority for remote servers.")


    @api.model
    def create(self, vals):
        if vals.get('name', False) and vals.get('name', False) in self.search([]).mapped('name'):
            raise UserError("Odoo Version with same Version Name already exists!!")

        if vals.get('is_multi_server', False) and not vals.get('default_saas_servers_ids', False):
            raise UserError("Select Atleast one Server in Default Saas Servers")

        res = super(SaasOdooVersion, self).create(vals)
        return res

    def write(self, vals):
        _logger.info(vals)
        if vals.get('name', False) and vals.get('name', False) in self.search([]).mapped('name'):
            raise UserError("Odoo Version with same Version Name already exists!!")
        
        if (vals.get('is_multi_server', False) or self.is_multi_server) and (not vals.get('default_saas_servers_ids', False) and not self.default_saas_servers_ids):
            raise UserError("Select Atleast one Server in Default Saas Servers")
        res = super(SaasOdooVersion, self).write(vals)
        return res

    @api.model
    def select_server(self):
        """
        Select Server in case of Remote server setup type according to their priority and number of clients.
        """
        for obj in self:
            if len(obj.default_saas_servers_ids):
                priority_list = list(obj.default_saas_servers_ids)
                priority_list.sort(key = lambda priority_record: priority_record.priority) 
                
                for priority in priority_list:
                    if priority.server_id.max_clients > priority.server_id.total_clients:
                        server = priority.server_id
                        break
                else:
                    return (False, 'All server limits over. Please create a new server!')
                return (True, server)

            else:
                return (False, 'Please select atleast one server in Default Saas servers')
    
    
    def drop_db_template(self):
        for obj in self:
            if obj.state != 'cancel':
                raise UserError("Cannot Drop Database: Active Saas odoo version(s) are linked to this DB")
            try:
                response = client.main(obj.db_template, None, {'server_type': 'self'}, get_module_resource('odoo_saas_kit'), from_drop_db=True, version=self.code or '16')
                if not response['db_drop']:
                    raise UserError("ERROR: Couldn't Drop Client Database. Please Try Again Later.\n\nOperation\tStatus\n\nDrop database: \t{}\n".format(response['db_drop']))
                else:
                    obj.is_drop_db = True
            except Exception as e:
                raise UserError(e)
