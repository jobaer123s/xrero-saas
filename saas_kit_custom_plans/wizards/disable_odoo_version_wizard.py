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


class DropOdooVersionDb(models.TransientModel):
    _name = "saas.odoo.version.db.unlink"

    name = fields.Char(string="Name")

    def drop_odoo_version_db(self):
        saas_odoo_version = self.env['saas.odoo.version'].browse([self.env.context.get('db_id')])
        saas_odoo_version.drop_db_template()