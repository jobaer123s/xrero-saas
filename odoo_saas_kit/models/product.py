# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)



class PrductTemplate(models.Model):
    _inherit = 'product.template'

    saas_plan_id = fields.Many2one(comodel_name="saas.plan", string="SaaS Plan", domain="[('state', '=', 'confirm')]",help="Id of related Saas Plan")


    def write(self,vals):
        if vals.get('website_published') or vals.get('is_published'):
            if self.saas_plan_id and self.saas_plan_id.state == 'draft':
                raise UserError("This product can't be published as the related SaaS Plan is in draft state!!")
        return super(PrductTemplate, self).write(vals)
    

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        template_id = vals.get('product_tmpl_id', False)
        if template_id:
            template_obj = self.env['product.template'].browse(template_id)
            vals['recurring_interval'] = template_obj.saas_plan_id and template_obj.saas_plan_id.recurring_interval
            vals['user_cost'] = template_obj.saas_plan_id and template_obj.saas_plan_id.user_cost
        product = super(ProductProduct, self).create(vals)
        return product

    recurring_interval = fields.Integer(string='Billing Cycle/Repeat Every',help="Repeat every (Days/Week/Month/Year)")
    is_user_pricing = fields.Boolean(string="User pricing", default=False,help="Check that user pricing is enable or not")
    per_user_pricing = fields.Boolean(string="Per User Pricing", related='saas_plan_id.per_user_pricing',help="Checkbox to enable the user product")
    user_cost = fields.Float(string="User cost", default=1.0,help="price for manage per user cost")

    @api.onchange('is_user_pricing')
    def check_is_user_pricing(self):
        for obj in self:
            if obj.is_user_pricing:
                obj.saas_plan_id = None

    @api.onchange('saas_plan_id')
    def check_is_saas_plan_id(self):
        for obj in self:
            if obj.saas_plan_id:
                obj.is_user_pricing = False
