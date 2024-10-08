# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Xrero Software Pvt. Ltd. (<https://Xrero.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.Xrero.com/license.html/>
# 
#################################################################################

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class ClientDisable(models.TransientModel):
    _name = "saas.instance.inactive"
    _description = "Saas Instance Inactive"
    

    name = fields.Char(string="Name")
    instance_id = fields.Integer(string="Instance Id")

    def inactive_client(self):
        record = self.env['saas.client'].browse([self.env.context.get('instance_id')])        
        record.inactive_client()

    def hold_contract(self):
        record = self.env['saas.contract'].browse([self.env.context.get('instance_id')])
        record.hold_contract()

    def drop_db(self):
        record = self.env['saas.client'].browse([self.env.context.get('instance_id')])        
        record.drop_db()

    def drop_container(self):
        record = self.env['saas.client'].browse([self.env.context.get('instance_id')])        
        record.drop_container()
