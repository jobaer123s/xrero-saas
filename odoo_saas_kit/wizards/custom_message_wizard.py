# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Xrero Software Pvt. Ltd. (<https://Xrero.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.Xrero.com/license.html/>
# 
#################################################################################

from odoo import api, models, fields
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

class CustomDomainWizard(models.TransientModel):
    _name = "custom.message.wizard"
    _description = "Custom Message Wizard"

    message = fields.Text(string="Message", readonly=True)
