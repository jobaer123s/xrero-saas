# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields, api, models
import logging
_logger = logging.getLogger(__name__)


class SaaSTrialSale(models.Model):
    _inherit = 'sale.order'

    def get_trial(self, product=None, quantity=None, saas_users=None):
        trial_product = product.saas_plan_id.trial_product
        line_config = self._cart_update(
            product_id=int(trial_product.id),
            add_qty=1,
        )
        for line in self.order_line:
            if line.id == line_config['line_id']:
                line.plan_product = product.id
                line.saas_users = saas_users
                break
        self._cr.commit()
        return True

    def create_trial_order(self, contract=None, new_contract=None, change_domain=None, from_trial=None):
        plan_line_config = self._cart_update(
            product_id=int(contract.invoice_product_id.id),
            add_qty=1
        )
        user_line_config = None
        if contract.per_user_pricing:
            saas_users = contract.saas_users
            price = saas_users * contract.invoice_product_id.user_cost
            user_line_config = self._cart_update(
                product_id=int(contract.invoice_product_id.saas_plan_id.user_product),
                add_qty=1
            )


        for line in self.order_line:
            if line.id == plan_line_config['line_id']:
                line.old_contract = contract.id
                line.from_trial = from_trial
                line.new_contract = new_contract
                if user_line_config:
                    line.plan_line_id = user_line_config['line_id']
                else:
                    break
            if user_line_config and line.id == user_line_config['line_id']:
                line.write({
                    'is_user_product': True,
                    'saas_users' : saas_users,
                    'price_unit' : price,
                    'linked_line_id': plan_line_config['line_id'], 
                })
        self._cr.commit()
        return True

    def process_contract(self):
        for order in self:
            trial_lines = list(filter(lambda line: (line.from_trial or line.plan_product) and not line.is_processed, order.order_line))
            for contract_line in trial_lines:
                contract_line.is_processed = True
                _logger.info(" -- -- - - - process contract executed in trial module ---")
                trial_started_date = False
                if contract_line.from_trial and not contract_line.new_contract:
                    order.contract_id = contract_line.old_contract
                    contract_line.old_contract.sale_order_line_id = contract_line.id
                    contract_line.old_contract.is_trial_enabled = False
                    if contract_line.old_contract.state == 'trial_expired':
                        contract_line.old_contract.state = 'confirm'
                    contract_line.old_contract.start_date = fields.Date.from_string(fields.Date.today())
                    contract_line.old_contract.total_cycles = contract_line.product_uom_qty
                    contract_line.old_contract.remaining_cycles = 0
                    recurring_interval_delta = relativedelta(months=(int(contract_line.old_contract.recurring_interval * contract_line.product_uom_qty)))                
                    contract_line.old_contract.next_invoice_date = fields.Date.from_string(fields.Date.today()) + recurring_interval_delta
                    self._cr.commit()
                    contract_line.old_contract.set_trial_data()
                    continue
                elif contract_line.from_trial and contract_line.new_contract:
                    contract_line.old_contract.state = 'trial_converted'
                    contract_line.old_contract.saas_client.stop_client()
                    contract_line.old_contract.start_date = fields.Date.from_string(fields.Date.today())
                    contract_product = contract_line.product_id
                    contract_rate = contract_line.price_unit
                    recurring_interval = contract_line.product_id.recurring_interval
                    total_cycles = contract_line.product_uom_qty
                    is_trial_enabled = False
                    trial_period = 0
                elif contract_line.product_id.saas_plan_id:
                    contract_product = contract_line.product_id
                    contract_rate = contract_line.price_unit
                    recurring_interval = contract_line.product_id.recurring_interval
                    total_cycles = contract_line.product_uom_qty
                    is_trial_enabled = False
                    trial_period = contract_product.saas_plan_id.trial_period
                elif contract_line.plan_product:
                    is_trial_enabled = True
                    trial_started_date = fields.Date.from_string(fields.Date.today())
                    contract_product = contract_line.plan_product
                    contract_rate = contract_line.plan_product.lst_price
                    recurring_interval = contract_line.plan_product.recurring_interval
                    total_cycles = 1
                    trial_period = contract_product.saas_plan_id.trial_period
                else:
                    contract_line.is_processed = False
                    continue
                saas_users = 0
                user_billing = 0
                if contract_product.saas_plan_id.per_user_pricing:
                    saas_users = contract_line.saas_users
                    user_billing = contract_product.user_cost * total_cycles # need to update this 
                relative_delta = relativedelta(days=trial_period)
                old_date = fields.Date.from_string(fields.Date.today())
                start_date = fields.Date.to_string(old_date + relative_delta)
                recurring_interval_delta = relativedelta(months=(int(recurring_interval * contract_line.product_uom_qty)))
                server_id = None
                if not contract_product.saas_plan_id.is_multi_server:
                    server_id = contract_product.saas_plan_id.server_id.id
                vals = dict(
                    partner_id=order.partner_id and order.partner_id.id or False,
                    recurring_interval=recurring_interval,
                    recurring_rule_type=contract_product.saas_plan_id.recurring_rule_type,
                    invoice_product_id=contract_product and contract_product.id or False,
                    pricelist_id=order.pricelist_id and order.pricelist_id.id or False,
                    currency_id=order.pricelist_id and order.pricelist_id.currency_id and order.pricelist_id.currency_id.id or False,
                    start_date=start_date,
                    total_cycles=total_cycles,
                    trial_period=trial_period,
                    remaining_cycles=0,
                    next_invoice_date=fields.Date.to_string(fields.Date.from_string(start_date) + recurring_interval_delta),
                    contract_rate=contract_rate,
                    contract_price=contract_rate * total_cycles,
                    per_user_pricing=contract_product.saas_plan_id.per_user_pricing,
                    user_cost=contract_product.user_cost,
                    due_users_price=contract_product.saas_plan_id.due_users_price,
                    saas_users=saas_users,
                    min_users=contract_product.saas_plan_id.min_users,
                    max_users=contract_product.saas_plan_id.max_users,
                    user_billing=user_billing,
                    total_cost=(contract_rate * total_cycles) + user_billing,
                    auto_create_invoice=False,
                    saas_module_ids=[(6, 0, contract_product.saas_plan_id.saas_module_ids.ids)],
                    on_create_email_template=self.env.ref('odoo_saas_kit.client_credentials_template').id,
                    is_multi_server=contract_product.saas_plan_id.is_multi_server,
                    server_id=server_id,
                    sale_order_line_id=contract_line.id,
                    plan_id=contract_product.saas_plan_id.id,
                    db_template=contract_product.saas_plan_id.db_template,
                    is_trial_enabled=is_trial_enabled,
                    trial_started_date=trial_started_date,
                )
                try:
                    record_id = self.env['saas.contract'].create(vals)
                    _logger.info("------VIA-ORDER--Contract--Created-------%r", record_id)
                except Exception as e:
                    _logger.info("-----VIA-ORDER---Exception-While-Creating-Contract-------%r", e)
                else:
                    if contract_line.from_trial and contract_line.new_contract:
                        contract_line.old_contract.converted_contract_id = record_id.id
                    order.contract_id = record_id and record_id.id
                    record_id.send_subdomain_email()
        
            res = super(SaaSTrialSale, self).process_contract()
            return res
