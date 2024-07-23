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

import logging

_logger = logging.getLogger(__name__)

class SaasModuleProduct(models.Model):
    _inherit = 'product.product'

    is_saas_module = fields.Boolean(string="For Saas Module", default=False)

    @api.onchange('is_saas_module')
    def change_saas_module(self):
        if self.is_saas_module:
            self.saas_plan_id = None
            self.is_user_pricing = False
            
    @api.onchange('is_user_pricing')
    def check_is_user_pricing(self):
        for obj in self:
            if obj.is_user_pricing:
                obj.saas_plan_id = None
                obj.is_saas_module = False
                
    @api.onchange('saas_plan_id')
    def check_is_saas_plan_id(self):
        for obj in self:
            if obj.saas_plan_id:
                obj.is_user_pricing = False
                obj.is_saas_module = False
