# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import fields, api, models
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

APPS_VIEW = [
    ('normal', 'Normal'),
    ('category', 'Catagorical')
]

Nature = [
    ('per_month', 'Per Month'),
    ('per_user', 'Per User')
]

RECURRING_RULE = [
    ('daily', 'Day(s)'),
    ('weekly', 'Week(s)'),
    ('monthly', 'Month(s)'),
    ('monthlylastday', 'Month(s) last day'),
    ('yearly', 'Year(s)')
]

class SaasConfig(models.TransientModel):
    _inherit = 'res.config.settings'


    is_odoo_version = fields.Boolean(string="Provide Version Selection", default=True)
    is_users = fields.Boolean(string="Provide User Selection", default=True)
    apps_view = fields.Selection(selection=APPS_VIEW, string="Apps View", default='normal')
    max_users = fields.Integer(string="Max Users")
    is_free_users = fields.Boolean(string="Provide free Users")
    free_users = fields.Integer(string="Free Users")
    user_cost = fields.Integer(string="Per User Cost")
    addons_path = fields.Char(string="Default Addons Path")
    reminder_period = fields.Integer(string="Reminder Starts")
    is_reminder_period = fields.Boolean(string="Enable Reminder", default=False)
    annual_discount= fields.Boolean(string="Enable Discount", default=False)
    discount_percent= fields.Float(string="Discount %", default=0.00)


    @api.constrains('discount_percent')
    def check_discount(self):
        _logger.info("------------in constraint-------------")
        if self.discount_percent>100.00:
            raise UserError('Discount cannot be more than 100%')

    def set_values(self):
        super(SaasConfig, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('res.config.settings', 'is_odoo_version', self.is_odoo_version)
        IrDefault.set('res.config.settings', 'is_users', self.is_users)
        IrDefault.set('res.config.settings', 'apps_view', self.apps_view)
        IrDefault.set('res.config.settings', 'max_users', self.max_users)
        IrDefault.set('res.config.settings', 'is_free_users', self.is_free_users)
        IrDefault.set('res.config.settings', 'free_users', self.free_users)
        IrDefault.set('res.config.settings', 'user_cost', self.user_cost)
        IrDefault.set('res.config.settings', 'addons_path', self.addons_path)
        IrDefault.set('res.config.settings', 'reminder_period', self.reminder_period)
        IrDefault.set('res.config.settings', 'is_reminder_period', self.is_reminder_period)
        IrDefault.set('res.config.settings', 'annual_discount', self.annual_discount)
        IrDefault.set('res.config.settings', 'discount_percent', self.discount_percent)
        return True

    def get_values(self):
        res = super(SaasConfig, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        res.update(
            {
                'is_odoo_version': IrDefault._get('res.config.settings', 'is_odoo_version'),
                'is_users': IrDefault._get('res.config.settings', 'is_users'),
                'apps_view': IrDefault._get('res.config.settings', 'apps_view') or 'normal',
                'max_users': IrDefault._get('res.config.settings', 'max_users') or -1,
                'is_free_users': IrDefault._get('res.config.settings', 'is_free_users'),
                'free_users': IrDefault._get('res.config.settings', 'free_users'),
                'user_cost': IrDefault._get('res.config.settings', 'user_cost') or 1,
                'addons_path': IrDefault._get('res.config.settings', 'addons_path') or '/opt/odoo/addons',
                'reminder_period': IrDefault._get('res.config.settings', 'reminder_period') or 3,
                'is_reminder_period': IrDefault._get('res.config.settings', 'is_reminder_period'),
                'annual_discount': IrDefault._get('res.config.settings', 'annual_discount'),
                'discount_percent': IrDefault._get('res.config.settings', 'discount_percent'),
            }
        )
        return res

