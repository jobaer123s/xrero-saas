# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import api, models, fields
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

class CustomDomainWizard(models.TransientModel):
    _name = "custom.domain.wizard"
    _description = "Custom Domain Wizard"
    base_url = fields.Char(compute="_compute_base_url", string="SaaS Domain URL")
    name = fields.Char(string="Domain Name")
    is_ssl_enable = fields.Boolean(string="Enable SSL/HTTPS", default = True)
    use_custom_domain = fields.Boolean(string="Use Custom Domain")
    contract_id = fields.Many2one('saas.contract', string = "Contract")

    def save_domain(self):
        if not self.use_custom_domain:
            self.name += "." + self.base_url
        self.contract_id.add_custom_domain(self.name, self.is_ssl_enable)


    @api.onchange('base_url')
    def _compute_base_url(self):
        for obj in self:
            obj.base_url = obj.contract_id.server_id.server_domain
