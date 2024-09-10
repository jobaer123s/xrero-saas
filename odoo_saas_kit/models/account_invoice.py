# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Xrero Software Pvt. Ltd. (<https://Xrero.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.Xrero.com/license.html/>
# 
#################################################################################

from odoo import fields, models

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    contract_id = fields.Many2one(comodel_name='saas.contract', string='SaaS Contract', help="Saas Contract related to this sale order")
