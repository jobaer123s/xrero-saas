# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

import logging
from odoo import fields, models
_logger = logging.getLogger(__name__)

class BillingHistory(models.Model):
    _name = 'user.billing.history'
    _description = "User Billing History"

    name = fields.Char(string="Entry Name",help="Unique name for the Invoice")
    date = fields.Date(string="Date")
    cycle_number = fields.Char(string="Cycle")
    due_users = fields.Integer(string="Due Users",help="New Users created after last billed month, other than purchased user and will be charged as per due user cost in Next Invoice")
    free_users = fields.Integer(string="Free Users", help="Count of internal users which are free with this Plan")
    puchased_users = fields.Integer(string="Purchased Users", help="Number of users purchased with Plan which can be created within the instance without any extra cost")
    due_users_price = fields.Float(string="Due Users Price",help="Price for due users")
    puchase_users_price = fields.Float(string="Purchase Users Price",help="Tota ammount of Purchased user i.e purchased_user*User_price")
    is_invoiced = fields.Boolean(string="Invoiced")
    final_price = fields.Float(string="Final User's Price",help="Total price of contract i.e plan price + user price")
    contract_id = fields.Many2one(comodel_name="saas.contract", string="Contract ID", help="The contract for which this invoice is generated")
