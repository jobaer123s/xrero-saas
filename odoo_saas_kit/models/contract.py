# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

import logging
import random
import re
from odoo import api, fields, models, tools, _
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode
from odoo.modules.module import get_module_resource
from odoo.exceptions import UserError, ValidationError
from odoo.addons.auth_signup.models.res_partner import random_token as generate_token
from . lib import query
from . lib import generate_ssl_custom_domain


_logger = logging.getLogger(__name__)

CONTRACT_STATE = [
    ('draft', "Draft"),
    ('open', "Open"),
    ('confirm', "Confirmed"),
    ('hold', 'On Hold'),
    ('expired',"Expired"),
    ('cancel', "Cancelled"),]


def random_token():
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.SystemRandom().choice(chars) for _ in range(20))


class SaasContract(models.Model):
    _name = 'saas.contract'
    _description = "Saas Contracts"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    @api.depends('db_template')
    def _compute_saas_domain_url(self):
        for obj in self:
            obj.saas_domain_url = obj.server_id.server_domain if (obj.server_id or not obj.is_multi_server) else 'to_be_fetch'

    name = fields.Char(string='Contract Name',help="Name of contract. Unique and auto generated ")

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        help="Related customer"
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id,
        help="Company of the related partner"
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        default=lambda s: s._default_journal(),
        domain="[('company_id', '=', company_id)]",
    )
    recurring_interval = fields.Integer(
        default=1,
        string='Billing cycle',
        help="Repeat every (Days/Week/Month/Year)",
    )
    recurring_rule_type = fields.Selection(
        [('daily', 'Day(s)'),
         ('weekly', 'Week(s)'),
         ('monthly', 'Month(s)'),
         ('monthlylastday', 'Month(s) last day'),
         ('yearly', 'Year(s)'),
         ],
        default='monthly',
        string='Recurrence',
        help="Specify Interval for automatic invoice generation.", readonly=True,
    )
   # per_user_pricing = fields.Boolean(string="Per User pricing")
   # user_cost = fields.Float(string="Per User Cost")
    invoice_product_id = fields.Many2one(comodel_name="product.product", string="Invoice Product")
    contract_rate = fields.Float(string="Contract Rate")
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
    )
    currency_id = fields.Many2one(comodel_name="res.currency",help="Currency (USD/EURO/RUPEES)")

    start_date = fields.Date(
        string='Purchase Date',
        required=True
    )
    invoice_ids = fields.One2many(comodel_name="account.move", inverse_name="contract_id", tracking = True,help="Related Invoices generated for the SaaS Contract")
    on_create_email_template = fields.Many2one('mail.template', default=lambda self: self.env.ref('odoo_saas_kit.client_credentials_template'), string="Client Creation Email Template")
    auto_create_invoice = fields.Boolean(string="Automatically create next invoice", tracking = True,help="Automatically generate the next Invoice for the Saas Contract")
    saas_client = fields.Many2one(comodel_name="saas.client", string="SaaS Client",help="Related Saas client for the SaaS Contract")
    saas_module_ids = fields.Many2many(comodel_name="saas.module", relation="saas_contract_module_relation", column1="contract_id", column2="module_id", string="Related Modules", tracking = True,help="Modules that are Installed in the Odoo Instance")
    state = fields.Selection(selection=CONTRACT_STATE, default="draft", string="Status", tracking = True,help="Current State of the Saas Contract")
    total_cycles = fields.Integer(string="Purchase Cycle (Remaining/Total)", default=1, tracking = True, help="Total Number of purchased billing cycle.")
    remaining_cycles = fields.Integer(string="Remaining Cycles", default=1, tracking = True,help="Number of remaining billing cycle")
    trial_period = fields.Integer(string="Trial Period(in days)", default=0, tracking = True, help="No of trial/free days")
    next_invoice_date = fields.Date(string="Next invoice date", tracking = True,help="Date for the Next Invoice")
    server_id = fields.Many2one(comodel_name="saas.server", string="SaaS Server",help="Server Id on whcih the client's odoo instace will be configured")
    is_multi_server = fields.Boolean(string="Deploy Client's on Remote Server", default=False)
    sale_order_id = fields.Many2one(comodel_name="sale.order", related="sale_order_line_id.order_id", string="Related Sale Order")
    sale_order_line_id = fields.Many2one(comodel_name="sale.order.line", string="Related Sale Order Line")
    under_process = fields.Boolean(string="Client Creation Under Process", default=False)
    token = fields.Char(string="Token")
    domain_name = fields.Char(string="Domain name",help="Unique domain name for the Odoo Instance")
    db_template = fields.Char(string="DB Template")
    plan_id = fields.Many2one("saas.plan", string="SaaS Plan",help="Realted Plan")
    user_data_updated = fields.Boolean(string="User data Updated")
    user_data_error = fields.Boolean(string="User data Update Error")
    invitation_mail_sent = fields.Boolean(string="Invitation Mail Sent")
    invitation_mail_error = fields.Boolean(string="Invitation Mail Error")
    subdomain_email_sent = fields.Boolean(string="Sent Subdomain Email", default=False)
    use_separate_domain = fields.Boolean(string="Use custom domain", default=False, tracking = True,help="Enable this to set the custom domain for your Odoo Instance")
    saas_domain_url = fields.Char(compute='_compute_saas_domain_url', string="SaaS Domain URL")
    is_contract_expiry_mail = fields.Integer(default=0)
    per_user_pricing = fields.Boolean(string="Is Per User Pricing", default=False, tracking = True,help="Price for 1 purchased User")
    user_cost = fields.Float(string="Per User Cost", tracking = True)
    saas_users = fields.Integer(string="No. of Users", tracking = True)
    free_users = fields.Integer(string="Free Users", default=0, tracking = True)
    min_users = fields.Integer(string="Min. No. of Users", tracking = True)
    max_users = fields.Integer(string="Max. No. of Users", tracking = True)
    contract_price = fields.Float(string="Contract Price", tracking = True)
    from_backend = fields.Boolean(string="Is from Backend", default=False)
    user_billing = fields.Float(string="User Billing")
    total_cost = fields.Float(string="Total Contract Cost", tracking = True)
    user_billing_history_ids = fields.One2many(comodel_name="user.billing.history", inverse_name='contract_id', string="User Billing History")
    due_users_price = fields.Float(string="Due users price", default=1.0)
    previous_cycle_user = fields.Integer(string="Previous User")
    client_state = fields.Selection(string="Client State", related='saas_client.state')
    custom_domain_ids = fields.One2many(comodel_name='custom.domain', inverse_name='contract_id', string="Subdomains")
    is_revoked= fields.Boolean(string="is all revoked", default=True)

    delivered_renew_mail = fields.Integer(string="Mail Delivered", default=0)
    renew_deadline_date = fields.Date(string = "Renew Deadline")

    active = fields.Boolean(string="Active", default=True)
    client_url = fields.Char(string="Domain name", compute="_saas_client_url",help="Url for the client's Odoo Instance")

    @api.model
    def _saas_client_url(self):
        for rec in self:
            if rec.saas_client and rec.saas_client.client_url:
                rec.client_url = rec.saas_client.client_url
            elif rec.domain_name:
                rec.client_url = "http://" + rec.domain_name + "." + rec.saas_domain_url
            else:
                rec.client_url = ""


    def print_logs(self, log_type, message, line_no):
        if log_type=='info':
            _logger.info("Saas Contract CONTRACT{} : {} at Line {}".format(self.id, message, line_no))
        elif log_type=='warn':
            _logger.info("Warning in Saas Contract CONTRACT{} : {} at Line {}".format(self.id, message, line_no))
        elif log_type=='error':
            _logger.info("Error in Saas Contract CONTRACT{} : {} at Line {}".format(self.id, message, line_no))
    
    @api.onchange('pricelist_id')
    def pricelist_id_change(self):
        self.currency_id = self.pricelist_id and self.pricelist_id.currency_id and self.pricelist_id.currency_id.id or False

    @api.model
    def _default_journal(self):
        company_id = self.env.context.get(
            'company_id', self.env.user.company_id.id)
        domain = [
            ('company_id', '=', company_id)]
        return self.env['account.journal'].search(domain, limit=1)

    @api.model
    def attach_modules(self, client_id=None):
        module_ids = self.saas_module_ids
        for module in module_ids:
            self.env['saas.module.status'].create(dict(
                module_id=module.id,
                client_id=client_id.id,
            ))

    def send_expiry_mail(self):
        for obj in self:
            template = self.env.ref('odoo_saas_kit.contract_expiry_template')
            mail_id = template.send_mail(obj.id)
            current_mail = self.env['mail.mail'].sudo().browse(mail_id)
            res = current_mail.send()
            obj.is_contract_expiry_mail = 2
            obj.message_post(body="Contract is expired and Expiry mail is sent to the Customer", subject="Expired")


    @api.model
    def check_contract_expiry(self):
        contracts = self.search([('state', 'in', ['confirm', 'hold']), ('remaining_cycles', '=', 0), ('next_invoice_date', '<=', fields.Date.today()), ('domain_name', '!=', False)])
        _logger.info(f"-------   Contract Expiry Cron ---{contracts.ids}---")
        for contract in contracts:
            _logger.info("----------records  %r    "%contract.id)
            contract.is_contract_expiry_mail = 1
            contract.send_expiry_mail()
            database = contract.saas_client and contract.saas_client.database_name or False
            _, db_server = contract.server_id.get_server_details()
            response = query.set_contract_expiry(database, str(True), db_server=db_server)
            if response.get('status'):
                contract.saas_client.restart_client()
            else:
                _logger.info("-------   Exception While writing on client's Instance ------")
            contract.write({'state': 'expired'})
            contract._cr.commit()



    @api.model
    def client_creation_cron_action(self):
        IrDefault = self.env['ir.default'].sudo()

        auto_create_client = IrDefault._get('res.config.settings', 'auto_create_client')
        if auto_create_client:
            contracts = self.search([('state', 'in', ['draft', 'open']), ('domain_name', '!=', False)])
            _logger.info("------CRON-ACTION-RECORDS------%r", contracts)
            k = []
            for contract in contracts:
                try:
                    res = contract.create_saas_client()
                    k.append(res)
                except Exception as e:
                    continue
            return k
        

# ==================RENEW MAIL CRON FUNCTION==========================#
    @api.model
    def renew_mail_cron_action(self):
        IrDefault = self.env['ir.default'].sudo()
        enable_renew_mail = IrDefault._get('res.config.settings', 'enable_renew_mail')
        enable_renew_mail_paid_contract = IrDefault._get('res.config.settings', 'enable_renew_mail_paid_contract')
        renew_period_paid_contract = IrDefault._get('res.config.settings', 'renew_period_paid_contract')
        no_of_mails_paid_contract = IrDefault._get('res.config.settings', 'no_of_mails_paid_contract')
        stop_client_paid_contract = IrDefault._get('res.config.settings', 'stop_client_paid_contract')
        drop_paid_contract = IrDefault._get('res.config.settings', 'drop_paid_contract')
        buffer_paid_contract = IrDefault._get('res.config.settings', 'buffer_paid_contract')
        if not enable_renew_mail:
            return
        if not enable_renew_mail_paid_contract:
            return
        if not renew_period_paid_contract:
            return
        starting_date = fields.Date.today() - relativedelta(days=renew_period_paid_contract)
        contracts = self.env['saas.contract'].sudo().search([ ('next_invoice_date', '>=', starting_date),('next_invoice_date', '<=', fields.Date.today()), ('state', '=', 'expired')])  # trial converted is added for now will update in future
        for contract in contracts:
            contract.renew_deadline_date = contract.next_invoice_date + relativedelta(days=renew_period_paid_contract)
            gap_factor = renew_period_paid_contract / no_of_mails_paid_contract
            next_period = renew_period_paid_contract - ((no_of_mails_paid_contract - contract.delivered_renew_mail)*gap_factor)
            # contract.send_renew_reminder_mail()
            # contract.delivered_renew_mail -=1
            if next_period <= 0 and contract.delivered_renew_mail != no_of_mails_paid_contract:
                contract.send_renew_reminder_mail()
            else:
                next_date = fields.Date.today() - relativedelta(days=next_period)
                if next_date <= contract.next_invoice_date and contract.delivered_renew_mail != no_of_mails_paid_contract:
                    contract.send_renew_reminder_mail()
            if contract.saas_client and contract.saas_client.container_id and stop_client_paid_contract and contract.delivered_renew_mail>=no_of_mails_paid_contract and contract.renew_deadline_date<=fields.Date.today():
                contract.saas_client.stop_client()
            if drop_paid_contract and contract.saas_client.state == "stop" and contract.next_invoice_date>= fields.Date.today()-relativedelta(days=(renew_period_paid_contract + buffer_paid_contract)):
                    contract.saas_client.inactive_client()
                    contract.saas_client.drop_container()
                    contract.saas_client.drop_db()


# ==================RENEW MAIL CRON FUNCTION==========================#
    def send_renew_reminder_mail(self):
        """
        Method called from check_reminder_contracts method define above to sent the reminder emails.
        """
        for obj in self:
            template = self.env.ref('odoo_saas_kit.contract_renew_mail_template')
            mail_id = template.send_mail(obj.id)
            current_mail = self.env['mail.mail'].sudo().browse(mail_id)
            res = current_mail.send()
            mail_number = str(obj.delivered_renew_mail)
            # mail_number = "First" if obj.delivered_renew_mail == 0 else "Second" if obj.delivered_renew_mail == 1 else "Third"
            obj.delivered_renew_mail += 1
            obj.message_post(body=mail_number+" Expiry mail sent to Custom", subject="Waring Mail")
            # if obj.delivered_renew_mail == 0:
                # obj.check_contract_expiry()



    @api.model
    def _compute_subdomain_token(self):
        token = random_token()
        contracts = self.env['saas.contract'].search([('token', '=', token), ('state', '!=', 'draft')])
        while contracts:
            token = random_token()
            contracts = self.env['saas.contract'].search([('token', '=', token), ('state', '!=', 'draft')])
        self.token = token

    def cancel_contract(self):
        for obj in self:
            if obj.state == "draft":
                obj.state = "cancel"
            else:
                if obj.saas_client and obj.saas_client.state == 'cancel':
                    obj.state = "cancel"              
                else:
                    raise UserError("Please Cancel the Linked client first before cancel the Contract.")

    def resume_contract(self):
        """
        Called from button on contract "Resume Contract Contract" to resume the normal working of client's instance.
        """
        for obj in self:
            if obj.state == "expired":
                database = obj.saas_client and obj.saas_client.database_name or False
                _, db_server = obj.server_id.get_server_details()
                response = query.set_contract_expiry(database, str(False), db_server=db_server)
                if response.get('status'):
                    obj.saas_client.restart_client()
                else:
                    _logger.info("---------    Error while Updating Contract expiry  data ---------")
                obj.write({'state': 'confirm'})
                obj._cr.commit()
                _logger.info("---------  Contract Resuming ---------")

    def update_user_data(self):
        """
        Called from The button "Set UserData in the Contract Form"
        """
        self.print_logs('info', 'called update_user_data', '257')
        for obj in self:
            if obj.plan_id.use_specific_user_template and not obj.plan_id.template_user_id:
                raise UserError("Database Template User ID Not Set!")
            elif obj.plan_id.template_user_id:
                try:
                    _ = int(obj.plan_id.template_user_id)
                except Exception as e:
                    raise UserError("Database Template ID Must be a Integer Value!")
            if not obj.saas_client.client_url or not obj.saas_client.database_name:
                raise UserError("Go to Saas Client record and Create Client Instance first!!!")
            token = generate_token()
            try:
                if obj.from_backend:
                    obj.generate_invoice(first_invoice=True)
                elif obj.per_user_pricing:
                    obj.update_billing_history(first=True)
                    obj.previous_cycle_user = max(obj.min_users, obj.saas_users)
            except Exception as e:
                raise UserError("Unable To Write User Data %r"%e)
            try:
                obj.sudo().set_user_data(token=token)
                obj._cr.commit()
                reset_pwd_url = "{}/web/signup?token={}&db={}".format(obj.saas_client.client_url, token, obj.saas_client.database_name)
                obj.saas_client.invitation_url = reset_pwd_url
            except Exception as e:
                _logger.info("--------EXCEPTION-WHILE-UPDATING-DATA-AND-SENDING-INVITE-------%r----", e)
                raise UserError('Exception while updating client data.')

    def send_invitation_email(self):
        for obj in self:
            if not obj.saas_client or (obj.saas_client and not obj.saas_client.client_url):
                obj.invitation_mail_error = True
                obj.invitation_mail_sent = False
                raise UserError("Unable To Send Invitation Email\nERROR: Make Sure That Client Url Is Created!")

            if obj.saas_client and obj.saas_client.client_url and (not obj.saas_client.invitation_url):
                obj.invitation_mail_error = True
                obj.invitation_mail_sent = False
                raise UserError("Unable To Send Invitation Email\nERROR: Please Set User Data First!")
            else:
                obj.invitation_mail_error = False
                obj.invitation_mail_sent = True
                template = obj.on_create_email_template
                mail_id = template.send_mail(obj.saas_client.id)
                current_mail = self.env['mail.mail'].sudo().browse(mail_id)
                current_mail.send()
                obj.write({'state': 'confirm'})
                self._cr.commit()


    def set_user_data(self, token=False):
        self.print_logs('info', 'called set_user_data', '304')
        for obj in self:
            data = dict()
            partner_id = obj.partner_id
            user_id = self.env['res.users'].search([('partner_id', '=', obj.partner_id.id)], limit=1)
            if not user_id and not partner_id.email:
                raise UserError("Please Specify The Email Of The Selected Partner!")
            host_server, db_server = obj.server_id.get_server_details()
            data['database'] = obj.saas_client and obj.saas_client.database_name or False
            data['user_id'] = obj.plan_id.use_specific_user_template and obj.plan_id.template_user_id and int(obj.plan_id.template_user_id)
            data['user_data'] = dict(
                name = user_id and user_id.name or partner_id.name or '',
                login = user_id and user_id.login or partner_id.email or '',
            )

            data['partner_data'] = dict(
                name = partner_id.name or '',
                street = partner_id.street or '',
                street2 = partner_id.street2 or '',
                city = partner_id.city or '',
                state_id = partner_id.state_id and partner_id.state_id.id or False,
                zip = partner_id.zip or '',
                country_id = partner_id.country_id and partner_id.country_id.id or False,
                phone = partner_id.phone or '',
                mobile = partner_id.mobile or '',
                email = partner_id.email or '',
                website = partner_id.website or '',
                signup_token=token or '',
                signup_type="signup",
            )
            data['host_server'] = host_server
            data['db_server'] = db_server
            _logger.info("------DATAAA-------%r", data)
            self.print_logs('info', 'calling update_user script', '337')
            response = query.update_user(**data)
            if response.get('status'):
                _logger.info("------1-------")
                obj.user_data_updated = True
                obj.user_data_error = False
                self._cr.commit()
                obj.message_post(
                    body="User Data Update Successfully",
                    subject="User Data Update Response",
                )
            else:
                _logger.info("------2-------")
                obj.user_data_updated = False
                obj.user_data_error = True
                self._cr.commit()
                raise UserError(f"Unable To Write User Data. {'Error: '+str(response['result']) if response['result'] else None}")
            if obj.per_user_pricing:
                vals = dict()
                vals['database'] = obj.saas_client and obj.saas_client.database_name or False
                vals['min_users'] = obj.min_users
                vals['max_users'] = obj.max_users
                try:
                    response = None
                    self.print_logs('info', 'calling set_user_limt script', '361')
                    response = query.set_user_limt(vals, db_server=db_server, is_count=True)
                except Exception as e:
                    _logger.info("-------Exception while updation limit %r -------"%e)    
                if response.get('status'):
                    obj.saas_client.restart_client()
                    _logger.info("---------   Updated User limits --------")
                else:
                    _logger.info("---------   Exception While updating user limits  ------")

    def send_subdomain_email(self):
        for obj in self:
            obj._compute_subdomain_token()
            template = self.env.ref('odoo_saas_kit.client_subdomain_template')
            mail_id = template.send_mail(obj.id)
            current_mail = self.env['mail.mail'].sudo().browse(mail_id)
            current_mail.send()
            self.print_logs('info', 'Subdomain mail sent successfully', '378')
            obj.subdomain_email_sent = True


    def get_subdomain_url(self):
        self.ensure_one()
        params = {
            'contract_id': self.id,
            'token': self.token,
            'partner_id': self.partner_id.id
        }
        return '/mail/contract/subdomain?' + url_encode(params)
                                

    # Used to confirm the contracts that are in Draft state but has a Client record associated with it. It created the client instance if already not created for a contract and then send the invitation email.
    def mark_confirmed(self):
        self.print_logs('info', 'called mark_confirmed', '394')
        for obj in self:
            if obj.saas_client.client_url:
                obj.send_invitation_email()
            else:
                if not obj.domain_name:
                    raise UserError("Please select a domain first!")
                if obj.under_process:
                    raise UserError("Client Creation Already Under Progress!")
                else:
                    domain_name = None
                    if obj.use_separate_domain:
                        domain_name = obj.domain_name
                    else:
                        domain_name = "{}.".format(obj.domain_name)
                    obj.under_process = True
                    self._cr.commit()
                
                obj.check_server_status()
                
                contracts = self.sudo().search([('domain_name', '=ilike', obj.domain_name), ('state', '!=', 'cancel')])
                if len(contracts) > 1:
                    _logger.info("---------ALREADY TAKEN--------%r", contracts)
                    obj.under_process = False
                    obj.domain_name = False
                    self._cr.commit()
                    raise UserError("This domain name is already in use! please try some other domain name!")

                obj.under_process = True
                self._cr.commit()

                if not obj.use_separate_domain:
                    domain_name = domain_name+'{}'.format(obj.saas_domain_url)

                if obj.server_id.max_clients <= obj.server_id.total_clients:
                    obj.under_process = False
                    self._cr.commit()
                    raise UserError("Maximum Clients limit reached!")
                
                custom_domains = [cst_dmn.name for contract in self.sudo().search([]) for cst_dmn in contract.custom_domain_ids if cst_dmn.status=='active']
                if domain_name in custom_domains:
                    _logger.info("---------ALREADY TAKEN IN CUSTOM DOMAIN--------")
                    obj.under_process = False
                    obj.domain_name = False
                    self._cr.commit()
                    raise UserError("This domain name is already in use as a custom domain! Please try some other domain name!")


                vals = dict(
                    saas_contract_id = obj.id,
                    partner_id = obj.partner_id and obj.partner_id.id or False,
                    server_id = obj.server_id.id,
                    # admin_username = obj.plan_id.db_template_username or False,
                    # admin_password = obj.plan_id.db_template_password or False,
                )
                if obj.saas_client:
                    obj.saas_client.write(vals)
                    client_id = obj.saas_client
                else:
                    client_id = self.env['saas.client'].create(vals)
                    obj.attach_modules(client_id)
                    obj.write({'saas_client': client_id.id})
                self._cr.commit()
                try:
                    client_id.fetch_client_url(domain_name)
                    _logger.info("--------Client--Created-------%r", client_id)
                except Exception as e:
                    obj.under_process = False
                    self._cr.commit()
                    _logger.info("--------Exception-While-Creating-Client-------%r", e)
                    raise UserError("Exception While Creating Client {}".format(e))
                else:
                    obj.write({'state': 'open'})
                    obj.under_process = False
                    self._cr.commit()
                    if client_id.client_url:
                        template = obj.on_create_email_template
                        mail_id = template.send_mail(client_id.id)
                        current_mail = self.env['mail.mail'].sudo().browse(mail_id)
                        res = current_mail.send()
                        self.print_logs('info', 'Client creds mail sent successfully', '464')
                        obj.write({'state': 'confirm'})
                        self._cr.commit()
                        return res

    def update_billing_history(self, first=None, arrear_users=None, arrear_price=None):
        """
        Used to create the billing history for contract, call while create client having first = True
        and  
        call every time when invoice is generated with first = False
        """
        if first:
            total_users = self.saas_users - self.free_users
            if total_users < 0:
                total_users = 0
            """
            Run For the first time when client is created
            """
            billing_history = self.env['user.billing.history'].create({
            'name': 'Data'+str(self.id),
            'date': fields.Date.today(),
            'cycle_number': 'Purchase',
            'due_users': 0,
            'free_users': self.free_users,
            'puchased_users': self.saas_users,
            'due_users_price': self.due_users_price or 1.0,
            'puchase_users_price': self.user_cost,
            'final_price': total_users * self.user_cost,
            'contract_id': self.id,
            'is_invoiced': False,
        })
            if billing_history:
                _logger.info("-----------Billing History Created ----------%r"%billing_history)
            else:
                _logger.info("-----------Exception while creating billing History---------- ")
        else:
            """
            Run at the time of invoice creation
            """
            if self.recurring_interval > 1:
                due_users = int(arrear_users)
                puchased_users = self.previous_cycle_user
            else:
                due_users = 0
                puchased_users = self.previous_cycle_user + int(arrear_users)
                arrear_price = 0
            total_users = puchased_users - self.free_users
            if total_users < 0:
                total_users = 0
            obj_history = self.env['user.billing.history'].create({
                'name': 'Data'+str(fields.Date.today()),
                'date': fields.Date.today(),
                'cycle_number': fields.Date.today().strftime("%B%Y"),
                'due_users': due_users,
                'free_users': self.free_users,
                'puchased_users': puchased_users,
                'due_users_price': self.due_users_price or 1.0,
                'puchase_users_price': self.user_cost,
                'contract_id': self.id,
                'final_price': (total_users*self.user_cost) + arrear_price,
                'is_invoiced': True,
            })
            if obj_history:
                _logger.info("-----------Billing History Updated ----------%r"%obj_history)
                # cost = (obj_history.puchased_users * obj_history.puchase_users_price) + (obj_history.due_users * obj_history.due_users_price)
                cost = obj_history.final_price
                new_users = obj_history.puchased_users + obj_history.due_users
                return {
                    'total_cost': cost,
                    'new_users' : new_users,
                }
            else:
                 _logger.info("-----------Exception while updating billing History---------- ")

    def check_server_status(self):
        """
        Method called from mark_as_confirmed and created_saas_client.
        To select the available sercer in case of multi server else to check the space on selected local server 
        """
        if self.is_multi_server:
            server_id = self.plan_id.select_server()
            if not server_id[0]:
                self.under_process = False
                self._cr.commit()
                raise UserError(server_id[1])
            self.write({
                'server_id': server_id[1].id,
                'saas_domain_url': server_id[1].server_domain,
            })
            self._cr.commit()
        else:    
            if self.server_id.max_clients <= self.server_id.total_clients:
                self.under_process = False
                self._cr.commit()
                raise UserError("Maximum Clients limit reached!")


    # Used to create the clients and share credentials for the contracts.
    def create_saas_client(self):
        self.print_logs('info', 'called create_saas_client', '563')
        for obj in self:
            if not obj.domain_name:
                raise UserError("Please select a domain first!")
            if obj.under_process:
                raise UserError("Client Creation Already Under Progress!")
            else:
                domain_name = None
                if obj.use_separate_domain:
                    domain_name = obj.domain_name
                else:
                    domain_name = "{}.".format(obj.domain_name)   # is edited

                obj.under_process = True
                self._cr.commit()
                obj.check_server_status()
                contracts = self.sudo().search([('domain_name', '=ilike', obj.domain_name), ('state', '!=', 'cancel')])
                if len(contracts) > 1:
                    _logger.info("---------ALREADY TAKEN--------%r", contracts)
                    obj.under_process = False
                    obj.domain_name = False
                    self._cr.commit()
                    raise UserError("This domain name is already in use! Please try some other domain name!")

                obj.under_process = True
                self._cr.commit()

                if not obj.use_separate_domain:
                    domain_name = domain_name+'{}'.format(obj.saas_domain_url)
                if obj.server_id.max_clients <= obj.server_id.total_clients:
                    obj.under_process = False
                    self._cr.commit()
                    raise UserError("Maximum Clients limit reached!")

                custom_domains = [cst_dmn.name for contract in self.sudo().search([]) for cst_dmn in contract.custom_domain_ids if cst_dmn.status=='active']
                if domain_name in custom_domains:
                    _logger.info("---------ALREADY TAKEN IN CUSTOM DOMAIN--------")
                    obj.under_process = False
                    obj.domain_name = False
                    self._cr.commit()
                    raise UserError("This domain name is already in use as a custom domain! Please try some other domain name!")


                vals = dict(
                    saas_contract_id = obj.id,
                    partner_id = obj.partner_id and obj.partner_id.id or False,
                    server_id = obj.server_id.id,
                )
                client_id = self.env['saas.client'].search([('saas_contract_id', '=', obj.id)])
                if client_id:
                    client_id.write(vals)
                else:
                    client_id = self.env['saas.client'].create(vals)
                self.print_logs('info', 'client record created/updated', '607')
                obj.attach_modules(client_id)
                obj.write({'saas_client': client_id.id})
                self._cr.commit()
                try:
                    client_id.fetch_client_url(domain_name)
                    _logger.info("--------Client--Created-------%r", client_id)
                except Exception as e:
                    obj.under_process = False
                    self._cr.commit()
                    _logger.info("--------Exception-While-Creating-Client-------%r", e)
                    raise UserError("Exception While Creating Client {}".format(e))
                else:
                    obj.write({'state': 'open'})
                    obj.under_process = False
                    self._cr.commit()
                    if client_id.client_url:
                        try:
                            token = generate_token()
                            _logger.info("--------------%r", token)
                            obj.sudo().set_user_data(token=token)
                            self._cr.commit()
                        except Exception as e:
                            _logger.info("--------EXCEPTION-WHILE-UPDATING-DATA-------%r----", e)
                            raise UserError(f"Exception While Updating Client Data {e}")
                        else:
                            reset_pwd_url = "{}/web/signup?token={}&db={}".format(client_id.client_url, token, client_id.database_name)
                            client_id.invitation_url = reset_pwd_url
                            template = obj.on_create_email_template
                            mail_id = template.send_mail(client_id.id)
                            current_mail = self.env['mail.mail'].sudo().browse(mail_id)
                            res = current_mail.send()
                            self.print_logs('info', 'Client creds mail sent successfully', '638')
                            obj.write({'state': 'confirm'})
                            self._cr.commit()
                            try:
                                if obj.from_backend:
                                    obj.generate_invoice(first_invoice=True)
                                elif obj.per_user_pricing:
                                    obj.update_billing_history(first=True)
                                    obj.previous_cycle_user = max(obj.min_users, obj.saas_users)
                            except Exception as e:
                                _logger.info("----------------  Exception While creating invoice-----------------")                            
                            return res

    def extend_contract(self):
        for obj in self:
            obj.total_cycles += 1
            obj.remaining_cycles += 1

    def calculate_arrear_price(self, arrer_response):
        total_price = 0
        text = ''
        for item in arrer_response.get('result'):
            total_price += (item[2] or 1) * self.due_users_price
            text += 'Name :'+item[0]+' Created in: '+item[1].strftime("%B%Y")+' Billed Months: '+str(item[2] or 1)+', \n'
        return {
            'arrear_users': len(arrer_response),
            'total_price': total_price,
            'text': text
        }

    def send_invoice_mail(self, invoice):
        """
        Method to mail the created invoice to the client autmotically
        """
        template = self.env.ref('account.email_template_edi_invoice')
        subjects = self.env['mail.template']._render_template(template.subject, 'account.move', [invoice.id]).get(invoice.id)
        body = template._render_template_qweb(template.body_html, 'account.move', [invoice.id]).get(invoice.id)
        emails_from = self.env['mail.template']._render_template(template.email_from,'account.move', [invoice.id]).get(invoice.id)
        mail_compose_obj = self.env['mail.compose.message'].sudo().create({
        'subject':subjects,
        'body':body,
        'parent_id':False,
        'email_from':emails_from,
        'model':'account.move',
        'res_ids':[int(invoice.id)],
        'record_name':invoice.name,
        'message_type':'comment',
        'composition_mode':'comment',
        'partner_ids':[invoice.partner_id.id],
        'auto_delete':False,
        'template_id':template.id,
        'email_add_signature':True,
        'subtype_id':1,
        'author_id':self.env.user.partner_id.id,
        })
        mail_compose_obj.with_context(custom_layout="mail.mail_notification_paynow",model_description='invoice')._action_send_mail()
        self.mapped('invoice_ids').write({'is_move_sent': True})

    # Used to create the next invoice for the contract
    def generate_invoice(self, first_invoice=None):
        for obj in self:
            if obj.remaining_cycles:
                user_count = None
                data = {}
                if obj.per_user_pricing:
                    if obj.saas_client and obj.saas_client.database_name:
                        _, db_server = obj.server_id.get_server_details()
                        response = query.get_user_count(obj.saas_client.database_name, db_server=db_server)
                        
                        if response.get('status'):
                            response = response.get('result')
                            user_count = response[0][0]
                        else:
                            raise UserError(response.get('message'))
                        if obj.plan_id.max_users != -1 and user_count > obj.plan_id.max_users:
                            raise UserError("Client have crossed the maximum user limit.")
                        user_count = max(user_count, obj.saas_users)
                        if user_count > obj.previous_cycle_user:
                            arrer_response = query.get_arrear_users(
                                obj.saas_client.database_name,
                                db_server=db_server,
                                limit = user_count - obj.previous_cycle_user,
                            )
                            if not arrer_response.get('status'):
                                raise UserError("Couldn't fetch arrer users! Please try again.")
                            data = obj.calculate_arrear_price(arrer_response)

                    if not user_count:
                        raise UserError("Couldn't fetch user count! Please try again later.")                    
                try:
                    price = None                    
                    if first_invoice == True:
                        if obj.per_user_pricing:
                            obj.update_billing_history(first=True)
                            obj.previous_cycle_user = max(obj.min_users, obj.saas_users)
                        price = obj.total_cost
                    else:
                        if obj.per_user_pricing:
                            res = obj.update_billing_history(arrear_users=data.get('arrear_users', 0), arrear_price=data.get('total_price', 0))
                            price = res.get('total_cost', 0) + obj.contract_rate
                            obj.previous_cycle_user = res.get('new_users', obj.previous_cycle_user)
                        else:
                            price = obj.contract_rate
                    
                    invoice_vals = {
                        'move_type': 'out_invoice',
                        'partner_id': obj.partner_id and obj.partner_id.id or False,
                        'currency_id': obj.pricelist_id and obj.pricelist_id.currency_id.id or False,
                        'contract_id': obj.id,
                        'invoice_line_ids': [(0, 0, {
                            'price_unit': price,
                            'quantity': 1.0,
                            'product_id': obj.invoice_product_id.id,
                        })],
                    }

                    invoice = self.env['account.move'].sudo().create(invoice_vals)
                    invoice.action_post()
                    obj.send_invoice_mail(invoice)
                    _logger.info("--------Invoice--Created-------%r", invoice)
                except Exception as e:
                    _logger.info("--------Exception-While-Creating-Invoice-------%r", e)
                    raise UserError("Exception While Creating Invoice: {}".format(e))
                else:
                    old_date = obj.next_invoice_date and fields.Date.from_string(obj.next_invoice_date) or fields.Date.from_string(fields.Date.today())
                    if first_invoice == True:
                        relative_delta = relativedelta(months=(self.recurring_interval*self.total_cycles))
                        obj.remaining_cycles = 0
                    else:    
                        relative_delta = relativedelta(months=self.recurring_interval)
                        obj.remaining_cycles -= 1
                    next_date = fields.Date.to_string(old_date + relative_delta)
                    obj.next_invoice_date = next_date
            else:
                raise UserError("This Contract Has Expired!")

    # Sends the subdomain selection url to the customer
    @api.model
    def get_subdomain_email(self, contract_id=None):
        self.browse(int(contract_id)).sudo().send_subdomain_email()

    # Sends the client credentials to the customer.
    # When the Contract is in Open state. Means the instance is created but the credentials haven't been shared yet.
    def send_credential_email(self):
        self.ensure_one()
        if not self.saas_client.client_url:
            raise UserError("SaaS Instance Not Found! Please create it from the associated client record for sharing the credentials.")
        
        template = self.on_create_email_template
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')


        if self.saas_client.invitation_url:
            try:
                token = generate_token()
                self.sudo().set_user_data(token=token)
                self._cr.commit()
                reset_pwd_url = "{}/web/signup?token={}&db={}".format(self.saas_client.client_url, token, self.saas_client.database_name)
                self.saas_client.invitation_url = reset_pwd_url
                self.state = 'confirm'
            except Exception as e:
                _logger.info("--------EXCEPTION-WHILE-UPDATING-DATA-AND-SENDING-INVITE-------%r----", e)
                raise UserError(f"Exception While Updating Client Data {e}")

            ctx = dict(
                default_model='saas.client',
                default_res_ids=[self.saas_client.id],
                default_use_template=bool(template),
                default_template_id=template and template.id or False,
                default_composition_mode='comment',
            )
            return {
                'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'view_id': compose_form.id,
                'target': 'new',
                'context': ctx,
            }
        else:
            raise UserError("SaaS Instance Not Found! Please create it from the associated client record for sharing the credentials.")


    @api.model
    def create_recurring_invoice(self):
        valid_contracts = self.search([('remaining_cycles', '>', 0), ('state', '=', 'confirm'), ('next_invoice_date', '<=', fields.Date.today()), ('auto_create_invoice', '=', True)])
        _logger.info("--------RECURRING-INVOICE-CRON--------%r", valid_contracts)

        for contract in valid_contracts:
            contract.generate_invoice()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('saas.contract')
        res = super(SaasContract,self).create(vals)
        res.message_subscribe(partner_ids=[res.partner_id.id])
        return res
    
    @api.model
    def hold_contract(self):
        for obj in self:
            obj.state = 'hold'
            if obj.saas_client and obj.saas_client.state == 'started':
                obj.saas_client.stop_client()

    def resume_hold_contract(self):
        for obj in self:
            if obj.state == 'hold':
                obj.state = 'confirm'
                if obj.saas_client and obj.saas_client.state == 'stopped':
                    obj.saas_client.start_client()


    def inactive_client(self):
        for obj in self:
            if obj.state == 'inactive' and obj.saas_client:
                if obj.saas_client.state == 'started':
                    obj.saas_client.stop_client()
                obj.saas_client.state = 'inactive'
    
    def write(self, vals):
        for obj in self:
            if vals.get('active')==False:
                if obj.state != 'cancel':
                    raise UserError("Please cancel the SaaS contract before archiving it.")
        if vals.get('domain_name'):
            if(vals.get('domain_name')[0]=='-' or vals.get('domain_name')[0]=='_'):
                raise UserError("Please enter a valid domain name.")
            regex = r"([a-zA-Z0-9_.-]+)"
            match = re.fullmatch(regex, vals.get('domain_name'))
            if match == None:
                raise UserError("Please enter domain name in only [a-zA-Z0-9] or [a-zA-Z0-9_.-] format with no blank spaces.")
        return super(SaasContract, self).write(vals)
    
    def unlink(self):
        for obj in self:
            if obj.saas_client:
                raise UserError("Error: You must delete the associated SaaS Client first!")
        return super(SaasContract, self).unlink()

    def add_custom_domain(self, domain=None, is_ssl=False):
        if not domain:
            raise UserError("Please Enter a Domain Name")
        
        contracts = self.sudo().search([('domain_name', 'like', domain.split('.')[0]), ('state', '!=', 'cancel')])
        if len(contracts) > 0:
            _logger.info("---------ALREADY TAKEN--------%r", contracts)
            raise UserError("This domain name is already in use! Please try some other domain name!")
        
        custom_domains = [cst_dmn.name for contract in self.sudo().search([]) for cst_dmn in contract.custom_domain_ids if cst_dmn.status=='active']
        if domain in custom_domains:
            _logger.info("---------ALREADY TAKEN IN CUSTOM DOMAIN--------")
            raise UserError("This domain name is already in use as a custom domain! Please try some other domain name!")
        module_path = get_module_resource('odoo_saas_kit')
        subdomain_name = self.domain_name
        if not self.use_separate_domain:
            subdomain_name += "."+self.saas_domain_url
        response = generate_ssl_custom_domain.main_add(subdomain_name.lower(), domain.lower(), is_ssl, module_path)
        if response.get('status'):
            vals = dict()
            vals['name'] = domain
            vals['contract_id'] = self.id
            vals['setup_date'] = fields.Date.today()
            vals['is_ssl_enable'] = is_ssl   
            self.env['custom.domain'].sudo().create(vals)
            self.is_revoked = False

            # Set the login_with_custom_domain field of related saas_client to True if any custom domain is added
            self.saas_client.login_with_custom_domain = True

        else:
            error = response.get('message')
            raise UserError(error)

    def revoke_subdomain(self, custom_domain=None):
        module_path = get_module_resource('odoo_saas_kit')
        response = generate_ssl_custom_domain.main_remove(custom_domain, module_path)
        if response.get('status'):
            domain_ids = self.custom_domain_ids.filtered(lambda r: r.status == "active" and r.name != custom_domain)
            self.is_revoked = not (domain_ids)

            # Set the login_with_custom_domain field of related saas_client to False if there is no any custom domain present
            if self.is_revoked:
                self.saas_client.login_with_custom_domain = False
            return response
        else:
            error = response.get('message')
            raise UserError("ER 502: {}".format(error))

    @api.model
    def redirect_invitation_url(self, contract_id=None):
        contract_id = self.browse(int(contract_id)).sudo()
        if contract_id.state == 'confirm' and contract_id.saas_client and contract_id.saas_client.invitation_url:
            login_url = contract_id.saas_client.invitation_url
        else:
            login_url = '/my'
        return login_url
        
