# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import models, api, fields
from dateutil.relativedelta import relativedelta
from odoo import fields, api, models
import datetime
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class SaasTrialWizard(models.TransientModel):
    _inherit = 'saas.contract.creation'

    def action_create_contract(self):
        for obj in self:
            trial_started_date = None
            if obj.trial_period:
                is_trial_enabled = True
                trial_started_date = fields.Date.from_string(fields.Date.today())
            else:
                is_trial_enabled = False
            if obj.recurring_interval <= 0:
                raise UserError("Default Billing Cycle can't be less than 1")
            if obj.trial_period < 0:
                raise UserError("Complimentary Free days can't be less than 0")
            if obj.per_user_pricing:
                obj.user_billing = obj.saas_users * obj.user_cost * obj.total_cycles
                if obj.saas_users < obj.min_users and obj.max_users != -1 and obj.saas_users > obj.max_users:
                    raise UserError("Please select number of users in limit {} - {}".format(obj.min_users, obj.max_users))
            obj.total_cost = obj.contract_price + obj.user_billing
            server_id = None
            if not obj.plan_id.is_multi_server:
                server_id = obj.plan_id.server_id.id
            vals = dict(
                partner_id=obj.partner_id and obj.partner_id.id or False,
                recurring_interval=obj.recurring_interval,
                recurring_rule_type=obj.recurring_rule_type,
                invoice_product_id=obj.invoice_product_id and obj.invoice_product_id.id or False,
                pricelist_id=obj.partner_id.property_product_pricelist and obj.partner_id.property_product_pricelist.id or False,
                currency_id=obj.partner_id.property_product_pricelist and obj.partner_id.property_product_pricelist.currency_id and obj.partner_id.property_product_pricelist.currency_id.id or False,
                start_date=obj.start_date,
                total_cycles=obj.total_cycles,
                trial_period=obj.trial_period,
                remaining_cycles=obj.total_cycles,
                next_invoice_date=obj.start_date,
                contract_rate=obj.contract_rate,
                contract_price=obj.contract_price,
                due_users_price=obj.due_users_price,
                total_cost=obj.total_cost,
                per_user_pricing=obj.per_user_pricing,
                user_billing=obj.user_billing,
                user_cost=obj.user_cost,
                saas_users=obj.saas_users,
                min_users=obj.min_users,
                max_users=obj.max_users,
                auto_create_invoice=obj.auto_create_invoice,
                saas_module_ids=[(6, 0, obj.plan_id.saas_module_ids.ids)],
                is_multi_server=obj.plan_id.is_multi_server,                
                server_id=server_id,
                db_template=obj.plan_id.db_template,
                plan_id=obj.plan_id.id,
                is_trial_enabled=is_trial_enabled,
                trial_started_date=trial_started_date,
                from_backend=True,
            )

            try:
                record_id = self.env['saas.contract'].create(vals)
                _logger.info("--------Contract--Created-------%r", record_id)
                if obj.plan_id._fields.get("plan_odoo_version"):
                    odoo_version_id = obj.plan_id.plan_odoo_version.id if obj.plan_id.plan_odoo_version else None
                    _logger.info(f"==SaasKitTrial=odoo_version_id====={odoo_version_id}==============")
                    write_ver = record_id.write({'odoo_version_id':odoo_version_id})
                    _logger.info(f"==SaasKitTrial===writeVer==odoo_version_id====={write_ver}==============")
            except Exception as e:
                _logger.info("--------Exception-While-Creating-Contract-------%r", e)
            else:
                imd = self.env['ir.model.data']
                # action = imd.xmlid_to_object('odoo_saas_kit.saas_contract_action')
                model, action  = imd.check_object_reference('odoo_saas_kit', 'saas_contract_action')
                action = self.env[model].sudo().browse([action])
                list_view_id = imd._xmlid_to_res_id('odoo_saas_kit.saas_contract_tree_view')
                form_view_id = imd._xmlid_to_res_id('odoo_saas_kit.saas_contract_form_view')

                return {
                    'name': action.name,
                    'res_id': record_id.id,
                    'type': action.type,
                    'views': [[form_view_id, 'form'], [list_view_id, 'tree'], ],
                    'target': action.target,
                    'context': action.context,
                    'res_model': action.res_model,
                }
