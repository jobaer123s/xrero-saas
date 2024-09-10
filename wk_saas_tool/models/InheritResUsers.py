# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################s

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, UserError
import logging
_logger = logging.getLogger(__name__)


class Users(models.Model):
    _inherit = "res.users"

    @api.model
    def _check_credentials(self, password, env):
        """ Override this method to plug additional authentication methods"""
        assert password
        self.env.cr.execute(
            "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
            [self.env.user.id]
        )
        [hashed] = self.env.cr.fetchone()
        valid, replacement = self._crypt_context()\
            .verify_and_update(password, hashed)
        if replacement is not None:
            self._set_encrypted_password(self.env.user.id, replacement)
        if not valid:
            if not hashed == password:
                raise AccessDenied()

    @api.model
    def create(self, vals):
        if vals.get('sel_groups_1_10_11') and vals['sel_groups_1_10_11'] == 1:
            try:
                max_users = self.env['ir.config_parameter'].sudo().get_param('user.max_users')
                is_user = self.env['ir.config_parameter'].sudo().get_param('user.count')
                if is_user == 'True' and int(max_users) != 0 and int(max_users) != -1:
                    total_active_users = self.env['res.users'].sudo().search([('active', '=', True), ('share', '=', False)])
                    if len(total_active_users) >= int(max_users):
                        raise Exception("User limit exceeds! Can't Create user.")
            except Exception as e:
                raise UserError("{} Please contact admin.".format(e))
        res = super(Users, self).create(vals)
        return res
    
    def write(self, vals):
        if vals.get('sel_groups_1_10_11') and vals['sel_groups_1_10_11'] == 1:
            try:
                max_users = self.env['ir.config_parameter'].sudo().get_param('user.max_users')
                is_user = self.env['ir.config_parameter'].sudo().get_param('user.count')
                if is_user == 'True' and int(max_users) != 0 and int(max_users) != -1:
                    total_active_users = self.env['res.users'].sudo().search([('active', '=', True), ('share', '=', False)])
                    if len(total_active_users) >= int(max_users):
                        raise Exception("User limit exceeds! Can't Create user.")
            except Exception as e:
                raise UserError("{} Please contact admin.".format(e))
        res = super(Users, self).write(vals)
        return res
