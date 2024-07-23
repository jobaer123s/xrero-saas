# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

import re
from odoo import models, api, fields, _
from odoo.exceptions import UserError

from odoo.modules.module import get_module_resource
from odoo.addons.odoo_saas_kit.models.lib import query
from odoo.addons.odoo_saas_kit.models.lib import saas
from . static_custom_plan import DEFAULT_ODOO_VERSION
import logging
_logger = logging.getLogger(__name__)


class SaasPlanCustomPlan(models.Model):
    _inherit= 'saas.plan'


    """
    Feature Addition: Version Selection from Backend
    
    """
    def _get_default_odoo_version(self):
        return self.env['saas.odoo.version'].search([('state', '=', 'confirm'),('code','=', DEFAULT_ODOO_VERSION)], limit=1).id

    provide_odoo_version = fields.Boolean(string="Provide Odoo Version", default=False)
    plan_odoo_version = fields.Many2one(string="Select Odoo Version", comodel_name="saas.odoo.version", domain="[('state', '=', 'confirm')]", default=_get_default_odoo_version)
    odoo_version_code = fields.Char(compute="_compute_odoo_version_code")

    ################################################################


    saas_module_ids = fields.Many2many(
        comodel_name="saas.module",
        relation="saas_plan_module_relation",
        column1="plan_id",
        column2="module_id",
        string="Related Modules",
        domain="[('odoo_version_id.code', '=', odoo_version_code)]")
    
    @api.onchange('plan_odoo_version')
    def _compute_odoo_version_code(self):
        self.odoo_version_code = self.plan_odoo_version.code if (self.provide_odoo_version and self.plan_odoo_version) else '17.0'
        # _logger.info(f"========self.odoo_version_code======{self.odoo_version_code}===========================")

    @api.depends('provide_odoo_version')
    def _set_plan_version_to_default(self):
       # if self.provide_odoo_version:
        _logger.info(f"======_set_plan_version_to_default===============")
        self.plan_odoo_version = self.env['saas.odoo.version'].search([('state', '=', 'confirm'),('code','=', DEFAULT_ODOO_VERSION)], limit=1).id
        _logger.info(f"======plan_odoo_version===={self.plan_odoo_version}======")

    def create_db_template(self):
        """
            Method to create the database template of the saas plan and confirm the state of the plan.
            Called from the Create Db Template button over saas plan.

            Update: Feature addition for custom odoo version selection
            Can be improved with super calling and updating super method with odoo version parameter
        """
        
        for obj in self:
            if not obj.db_template:
                raise UserError("Please select the DB template name first.")
            if re.match("^template_",obj.db_template):
                raise UserError("Couldn't Create DB. Please try again with some other Template Name!")
            db_template_name = "template_{}".format(obj.db_template)
            config_path = get_module_resource('odoo_saas_kit')
            status_module = obj.create_status_modules()
            installable_modules = obj.get_installable_modules()
            modules = [module.technical_name for module in installable_modules]            
            modules.append('wk_saas_tool')

            ####added selected odoo version in for plan db creation###
            odoo_version = obj.odoo_version_code
            ################################
            try:
                host_server, db_server = obj.server_id.get_server_details()
                response = saas.create_db_template(
                    db_template=db_template_name,
                    modules=modules,
                    config_path=config_path,
                    host_server=host_server,
                    db_server=db_server,
                    version=odoo_version)
                ##Updated the create_db_template parameters, added version for custom version
                
            except Exception as e:
                _logger.info("--------DB-TEMPLATE-CREATION-EXCEPTION-------%r", e)
                raise UserError(e)
            else:
            # response = True
                if response:
                    if response.get('status', False):
                        obj.db_template = db_template_name
                        obj.state = 'confirm'
                        obj.container_id = response.get('container_id', False)
                        # _logger.info("-= =- =- =-= -= -= %r-= -= = =-= "%installable_modules)
                        for module in installable_modules:
                            module.status="installed"
                            if not self.get_installable_modules():
                                self.is_all_installed=True
                            # _logger.info(f"============Status======={self.env['saas.module.status'].browse(id).status}=============")

                    else:
                        msg = response.get('msg', False)
                        if msg:
                            raise UserError(msg)
                        else:
                            raise UserError("Unknown Error. Please try again later with some different Template Name")
                else:
                    raise UserError("No Response. Please try again later with some different Template Name")


    def login_to_db_template(self):
        """
            Overridden for db(version) in login url
            #Called from the Login button over saas plan
            #Redict to the Plan instance to login in to template database
            Need improvement, can done by calling super and updating super method with version parameter
        """
        
        for obj in self:
            host_server, db_server = obj.server_id.get_server_details()
            response = query.get_credentials(
                obj.db_template,
                host_server=host_server,
                db_server=db_server)
            if response.get('status'):
                response = response.get('result')
                login = response[0][0]
                password = response[0][1]
                # login_url = "http://db16_templates.{}/saas/login?db={}&login={}&passwd={}".format(obj.saas_base_url,obj.db_template, login, password)
                login_url = "http://db{}_templates.{}/saas/login?db={}&login={}&passwd={}".format(obj.odoo_version_code.split('.')[0],obj.saas_base_url,obj.db_template, login, password)


                _logger.info("$$$$$$$$$$$$$$%r", login_url)
                return {
                    'type': 'ir.actions.act_url',
                    'url': login_url,
                    'target': 'new',
                }
            else:
                raise UserError("ERR001: "+str(response.get('message')))
