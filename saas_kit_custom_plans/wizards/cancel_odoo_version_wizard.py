# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class DropOdooVersionCancel(models.TransientModel):
    _name = "saas.odoo.version.cancel"

    name = fields.Char(string="Name")

    def cancel_odoo_version(self):
        saas_odoo_version = self.env['saas.odoo.version'].browse([self.env.context.get('db_id')])        
        # _logger.info("=========== saas_odoo_version ========= %r", saas_odoo_version)
        if saas_odoo_version.state == "open":
            saas_odoo_version.write({'is_drop_db': True,'state': 'cancel'})
        else:
            saas_odoo_version.write({'state': 'cancel'})
