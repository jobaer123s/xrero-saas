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


class DropPlanDb(models.TransientModel):
    _name = "saas.plan.db.unlink"
    _description = "Saas Plan DB Unlink"

    name = fields.Char(string="Name")
    db_id = fields.Integer(string="DB Plan Id")

    def drop_db_plan(self):
        record = self.env['saas.plan'].browse([self.env.context.get('db_id')])        
        record.drop_template()
