# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import fields, models, api
from odoo.exceptions import UserError

class SaasModule(models.Model):
    _name = 'saas.module'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Class for creating Modules that one wishes to provide as a service.'

    name = fields.Char(string="Name", required=True, tracking = True,help="Name of the module")
    image = fields.Binary(string='Image',help="Image of the module")
    technical_name = fields.Char(string="Technical Name", required=True, tracking=True,help="Technical name of the module")
    categ_id = fields.Many2one(comodel_name="saas.module.category", string="Module Category", tracking=True,help="Category under which this module exist")
    description = fields.Char('Description', help='Short description of module', tracking = True)
    active = fields.Boolean(string="Active", default=True, tracking=True)


    def unlink(self):
        for rec in self:
            if rec.env['saas.module.status'].search([('module_id','=',rec.id)]):
                raise UserError("Delete the linked client first")
        
        res = super(SaasModule,self).unlink()
        return res
