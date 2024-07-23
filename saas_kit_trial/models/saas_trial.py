# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
from odoo import fields, api, models
import datetime
import logging
_logger = logging.getLogger(__name__)


class SaaSTrialPlan(models.Model):
    _inherit = 'saas.plan'

    trial_product = fields.Many2one(comodel_name="product.product", string="Trial Product", domain="[('is_trial_price', '=', True)]")

    @api.onchange('trial_period')
    def check_trial_product(self):
        if self.trial_period == 0:
            self.trial_product = None

class SaasTrialProduct(models.Model):
    _inherit = 'product.product'

    is_trial_price = fields.Boolean(string="Is Trial Product")

    @api.onchange('is_trial_price')
    def check_is_user_pricing(self):
        for obj in self:
            if obj.is_trial_price:
                obj.saas_plan_id = None
                obj.is_user_pricing = None


class SaaSTrialOrderLine(models.Model):
    _inherit = 'sale.order.line'

    plan_product = fields.Many2one(comodel_name="product.product", string="Plan's Product")
    from_trial = fields.Boolean(string="Created from Trial")
    new_contract = fields.Boolean(string="New Contract")
    old_contract = fields.Many2one(comodel_name="saas.contract")
