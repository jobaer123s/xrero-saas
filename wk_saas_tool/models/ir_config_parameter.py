# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import api, fields, models
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class IrConfig(models.Model):
        _inherit = 'ir.config_parameter'

        @api.model
        def get_config_data(self):
            data = dict()
            self._cr.commit()
            data['trial.is_trial_enabled'] = self.env['ir.config_parameter'].sudo().get_param('trial.is_trial_enabled')
            trial_period = int(self.env['ir.config_parameter'].sudo().get_param('trial.trial_period'))
            data['trial.purchase_link'] = self.env['ir.config_parameter'].sudo().get_param('trial.purchase_link')
            create_date = self.env['ir.config_parameter'].sudo().get_param('database.create_date')
            create_date = datetime.strptime(create_date, '%Y-%m-%d %H:%M:%S')
            trial_date = create_date + timedelta(days=trial_period)
            data['contract.is_expired'] = self.env['ir.config_parameter'].sudo().get_param('contract.is_expired')
            _logger.info("##########################   %r         "%data)
            today_date = datetime.now()
            trial_period = (trial_date - today_date).days + 1
            if trial_period < 0:
                data['trial.trial_period'] = str(0)
            else:
                data['trial.trial_period'] = str(trial_period)
            return data
