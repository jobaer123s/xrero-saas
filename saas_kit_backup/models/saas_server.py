# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    You should have received a copy of the License along with this program.
#    If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import models, fields, tools
from odoo.exceptions import UserError


import logging
_logger = logging.getLogger(__name__)


LOCATION = [
    ('local', 'Local'),
]


class SaasServerBackup(models.Model):
    _inherit = 'saas.server'
    
    
    backup_location = fields.Selection(selection=LOCATION, string="Backup Location", default='local')
    retention = fields.Integer(string="Backup Retention")
