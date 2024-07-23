# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import http, _
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class TrialController(http.Controller):

    @http.route('/saas/trial/add/product', type='json', auth='public', website=True)
    def saas_trial_cart(self, product_id=None, quantity=None, saas_users=None, **kwargs):
        sale_order = request.website.sale_get_order(force_create=1)
        product = request.env['product.product'].sudo().search([('id', '=', product_id)])
        if sale_order.order_line:
            for line in sale_order.order_line:
                if line.product_id == product.saas_plan_id.trial_product:
                    return
        if sale_order and product_id:
            return sale_order.get_trial(product=product, quantity=quantity, saas_users=saas_users)

    @http.route('/saa/trial/pay_now', type="json", auth="public", website=True)
    def pay_for_trial(self, contract_id=None, from_trial=None, new_contract=None, **kwargs):
        sale_order = request.website.sale_get_order(force_create=1)
        contract = request.env['saas.contract'].sudo().search([('id', '=', contract_id)])
        if contract and sale_order:
            return sale_order.create_trial_order(contract=contract, new_contract=new_contract, from_trial=from_trial)
