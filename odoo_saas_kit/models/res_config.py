# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = 'Class for managing global SaaS settings.'

    auto_create_client = fields.Boolean(string="Automatically create clients from contract via Scheduler.",help="Automatically create clients from contract via Scheduler.")
    enable_renew_mail = fields.Boolean(string="Send Renew mail to continue the contract")
    enable_renew_mail_paid_contract = fields.Boolean(string="Send Renew mail to continue the paid contract")
    renew_period_paid_contract = fields.Integer(string="Renew Ends for paid contract")
    no_of_mails_paid_contract = fields.Integer(string="No of Renew Mail for paid contract", default = 3)
    stop_client_paid_contract = fields.Boolean(string="Stop client after last warning")
    drop_paid_contract = fields.Boolean(string="Delete Saas client")
    buffer_paid_contract = fields.Integer(string="Buffer Period")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('res.config.settings', 'auto_create_client', self.auto_create_client)
        IrDefault.set('res.config.settings', 'enable_renew_mail', self.enable_renew_mail)
        IrDefault.set('res.config.settings', 'enable_renew_mail_paid_contract', self.enable_renew_mail_paid_contract)
        IrDefault.set('res.config.settings', 'renew_period_paid_contract', self.renew_period_paid_contract)
        IrDefault.set('res.config.settings', 'no_of_mails_paid_contract', self.no_of_mails_paid_contract)
        IrDefault.set('res.config.settings', 'stop_client_paid_contract', self.stop_client_paid_contract)
        IrDefault.set('res.config.settings', 'drop_paid_contract', self.drop_paid_contract)
        IrDefault.set('res.config.settings', 'buffer_paid_contract', self.buffer_paid_contract)
        return True

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        res.update(
            {
                'auto_create_client': IrDefault._get('res.config.settings', 'auto_create_client'),
                'enable_renew_mail': IrDefault._get('res.config.settings', 'enable_renew_mail'),
                'enable_renew_mail_paid_contract': IrDefault._get('res.config.settings', 'enable_renew_mail_paid_contract'),
                'renew_period_paid_contract': IrDefault._get('res.config.settings', 'renew_period_paid_contract'),
                'no_of_mails_paid_contract': IrDefault._get('res.config.settings', 'no_of_mails_paid_contract'),
                'stop_client_paid_contract': IrDefault._get('res.config.settings', 'stop_client_paid_contract'),
                'drop_paid_contract': IrDefault._get('res.config.settings', 'drop_paid_contract'),
                'buffer_paid_contract': IrDefault._get('res.config.settings', 'buffer_paid_contract'),
            }
        )
        return res
