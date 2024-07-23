from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)



class PlanReset(models.TransientModel):
    _name = "saas.plan.reset"
    _description = 'Contract Creation Wizard.'

    plan_id = fields.Many2one(comodel_name="saas.plan", string="Related SaaS Plan", required=False)

    def action_reset_plan(self):
        for obj in self.plan_id:
            obj.state = 'draft'
            for res in obj.product_template_ids:
                logging.info(f"============res==========={res}")
                res.website_published = False

    @api.onchange('plan_id')
    def plan_id_change(self):
       for obj in self.plan_id:
            contracts = self.env['saas.contract'].search([('plan_id', '=', obj.id)])
            if contracts:
                raise UserError("This plan has some contracts associated with it!")