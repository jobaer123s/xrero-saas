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
from odoo.exceptions import UserError
from odoo.addons.website_sale.controllers import main

from odoo.addons.odoo_saas_kit.controllers.main import MailController
from werkzeug.exceptions import Forbidden

import logging

_logger = logging.getLogger(__name__)


class CustomMailController(MailController):
    _cp_path = '/mail'

    @http.route(['/mail/confirm_domain'], type='json', auth="public", methods=['POST'], website=True)
    def confirm_domain(self, domain_name, contract_id,  **kw):
        contract = request.env['saas.contract'].sudo().browse(int(contract_id))
        if contract.is_custom_plan and not contract.server_id:
            if contract.odoo_version_id and contract.odoo_version_id.is_multi_server:
                server_res = contract.odoo_version_id.select_server()
                if server_res and server_res[0]:
                    server_id = server_res[1]
            else:    
                server_id = request.env['saas.server'].sudo().search([('state', '=', 'confirm'), ('max_clients', '>' , 'total_clients')])
            contract.server_id = server_id.id
        res = super(CustomMailController, self).confirm_domain(domain_name, contract_id, **kw)
        return res
        


class PlanPage(http.Controller):

    def _create_custom_plan_data(self, *ver):
        data = dict()
        IrDefault = request.env['ir.default'].sudo()
        version_code= ver[0] if ver else None
        data['is_odoo_version'] = IrDefault._get('res.config.settings', 'is_odoo_version')

        data['odoo_version'] = version_code if version_code else request.env['saas.odoo.version'].sudo().search([('state', '=', 'confirm')]) if data['is_odoo_version'] else request.env['saas.odoo.version'].sudo().search([('state', '=', 'confirm'), ('code', '=', '17.0')], limit=1)
        if not data['odoo_version']:
            data.clear()
            data['error'] = "Odoo Version not found."
            _logger.info("======== Error - Odoo Version not found. ==========")
            return data
        modules = request.env['saas.module'].sudo().search([('is_published', '=', True),('odoo_version_id.code','=',version_code if version_code else data['odoo_version'][0].code)])

        data['is_users'] = IrDefault._get('res.config.settings', 'is_users')
        data['annual_discount'] = IrDefault._get('res.config.settings', 'annual_discount')
        data['discount_percent'] = IrDefault._get('res.config.settings', 'discount_percent')
        apps_view = IrDefault._get('res.config.settings', 'apps_view')
        if apps_view == 'normal':
            data['normal_view'] = True
            data['categorical_view'] = False
        else:
            data['normal_view'] = False
            data['categorical_view'] = True
        data['categories'] = dict()            
        for module in modules:
            if not module.categ_id:
                if data['categories'].get('DEFAULT'):
                    data['categories']['DEFAULT'].append(module)                 
                else:
                    data['categories']['DEFAULT'] = [module]                 
            elif data['categories'].get(module.categ_id.name.upper()):
                data['categories'][module.categ_id.name.upper()].append(module)
            else:
                data['categories'][module.categ_id.name.upper()] = [module]

        data['max_users'] = IrDefault._get('res.config.settings', 'max_users')
        data['is_free_users'] = IrDefault._get('res.config.settings', 'is_free_users')
        if data['is_free_users']:
            data['free_users'] = IrDefault._get('res.config.settings', 'free_users')
            data['is_free_users'] = True if data['free_users'] else False
        else:
            data['free_users'] = 0
        data['costing_nature'] = IrDefault._get('res.config.settings', 'costing_nature')
        data['user_cost'] = IrDefault._get('res.config.settings', 'user_cost')
        data['odoo_version'] = request.env['saas.odoo.version'].sudo().search([('state', '=', 'confirm')]) if data['is_odoo_version'] else request.env['saas.odoo.version'].sudo().search([('state', '=', 'confirm'), ('code', '=', '17.0')], limit=1)
        if not data['is_users']:
            data['costing_nature'] = 'per_month'
        data['company'] = request.env.company
        data['modules'] = modules
        return data
    
    def _create_custom_plan_normal_data(self,version_code):
        data=dict()
        data['version_code'] = version_code
        data['modules']= request.env['saas.module'].sudo().search([('is_published', '=', True),('odoo_version_id.code','=',version_code)])
        data['company'] = request.env.company
        return data


    @http.route('/custom/plan', type='http', auth="public",  website=True)
    def custom_plan_redirect(self):
        data = self._create_custom_plan_data()
        return request.render('saas_kit_custom_plans.plan_page', data)


    @http.route('/custom/version/categ', type='json', auth="public",  website=True)
    def custom_plan_redirect_version_categ(self, version_code):
        data = self._create_custom_plan_data(version_code)
        return request.env['ir.ui.view'].sudo()._render_template('saas_kit_custom_plans.category_view_template', data)

    @http.route('/custom/version/normal', type='json', auth="public",  website=True)
    def custom_plan_redirect_version_normal(self, version_code):
        data = self._create_custom_plan_normal_data(version_code)        
        return request.env['ir.ui.view'].sudo()._render_template('saas_kit_custom_plans.normal_view_template',data)


    @http.route('/saas/add/plan', type='json', auth='public', website=True)
    def saas_custom_plan_cart(self, apps=None, saas_users=None, version_name=None, total_cost=None, users_cost=None, recurring_interval=None, version_code=None , **kwargs):
        odoo_version_id = request.env['saas.odoo.version'].sudo().search([('code', '=', version_code), ('name', '=', version_name)], limit=1)        
        product_id = odoo_version_id.product_id        
        module_ids = []
        for module in apps:
            module_rec = request.env['saas.module'].sudo().search([('technical_name', '=', module), ('odoo_version_id.code', '=', odoo_version_id.code)])
            module_ids.append(module_rec.id)
        sale_order = request.website.sale_get_order(force_create=1)
        if sale_order and product_id:
            return sale_order.create_custom_contract_line(product_id=product_id, odoo_version_id=odoo_version_id, saas_users=saas_users, total_cost=total_cost, users_cost=users_cost, recurring_interval=recurring_interval, module_ids=module_ids)

    @http.route('/show/categ/view', type='http', auth='public', website=True)
    def show_categ_view(self,version_code):
        data = self._create_custom_plan_data(version_code)        
        return request.render('saas_kit_custom_plans.category_view_template', data)
        
    @http.route('/show/normal/view', type='http', auth='public', website=True)
    def show_normal_view(self,version_code):
        data = self._create_custom_plan_data(version_code)
        return request.render('saas_kit_custom_plans.normal_view_template', data)

    @http.route('/show/selected/apps/view', type='http', auth='public', website=True)
    def show_selected_apps_view(self):
        data = self._create_custom_plan_data()
        return request.render('saas_kit_custom_plans.select_apps_section', data)

    @http.route('/my/saas/contract/add/apps', type='json', auth="public",  website=True)
    def add_apps_contract_view(self, apps, contract_id):
        contract = request.env['saas.contract'].sudo().browse(int(contract_id))
        token = request.env['saas.contract'].add_apps(apps, contract_id)
        values={
            'contract': contract,
            'access_token': token
            }
        return request.env['ir.ui.view'].sudo()._render_template('odoo_saas_kit.portal_apps_template', values)


class SaasWebsiteSale(main.WebsiteSale):
#class for overriding controller for maintaining price on website sale (for v16)

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True, sitemap=False)
    def confirm_order(self, **post):
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order) or self.checkout_check_address(order)
        if redirection:
            return redirection

        order.order_line._compute_tax_id()
        
        request.session['sale_last_order_id'] = order.id

        if order.order_line.plan_line_id or order.order_line.saas_module_ids:
            request.website.sale_get_order()
        else:
            request.website.sale_get_order(update_pricelist=True)


        extra_step = request.website.viewref('website_sale.extra_info')
        if extra_step.active:
            return request.redirect("/shop/extra_info")

        return request.redirect("/shop/payment")

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        mode = (False, False)
        can_edit_vat = False
        values, errors = {}, {}

        partner_id = int(kw.get('partner_id', -1))

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ('new', 'billing')
            can_edit_vat = True
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                    mode = ('edit', 'billing')
                    can_edit_vat = order.partner_id.can_edit_vat()
                else:
                    shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
                    if order.partner_id.commercial_partner_id.id == partner_id:
                        mode = ('new', 'shipping')
                        partner_id = -1
                    elif partner_id in shippings.mapped('id'):
                        mode = ('edit', 'shipping')
                    else:
                        return Forbidden()
                if mode and partner_id != -1:
                    values = Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ('new', 'shipping')
            else: # no mode - refresh without post?
                return request.redirect('/shop/checkout')

        # IF POSTED
        if 'submitted' in kw and request.httprequest.method == "POST":
            pre_values = self.values_preprocess(kw)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

            if errors:
                errors['error_message'] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)
                # We need to validate _checkout_form_save return, because when partner_id not in shippings
                # it returns Forbidden() instead the partner_id
                if isinstance(partner_id, Forbidden):
                    return partner_id
                if mode[1] == 'billing':
                    order.partner_id = partner_id
                    # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
                    order.partner_invoice_id = partner_id
                    if not kw.get('use_same'):
                        kw['callback'] = kw.get('callback') or \
                            (not order.only_services and (mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
                    # We need to update the pricelist(by the one selected by the customer), because onchange_partner reset it
                    # We only need to update the pricelist when it is not redirected to /confirm_order
                    
############UPDATE START#FOR SAAS###########################
                    if kw.get('callback', '') != '/shop/confirm_order':
                        if order.order_line.plan_line_id or order.order_line.saas_module_ids:
                            request.website.sale_get_order()
                        else:
                            request.website.sale_get_order(update_pricelist=True)
                        # request.website.sale_get_order(update_pricelist=True)
###########################UPDATE END#######################
                elif mode[1] == 'shipping':
                    order.partner_shipping_id = partner_id

                # TDE FIXME: don't ever do this
                # -> TDE: you are the guy that did what we should never do in commit e6f038a
                order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                if not errors:
                    return request.redirect(kw.get('callback') or '/shop/confirm_order')

        render_values = {
            'website_sale_order': order,
            'partner_id': partner_id,
            'mode': mode,
            'checkout': values,
            'can_edit_vat': can_edit_vat,
            'error': errors,
            'callback': kw.get('callback'),
            'only_services': order and order.only_services,
            'account_on_checkout': request.website.account_on_checkout,
            'is_public_user': request.website.is_public_user()
        }
        render_values.update(self._get_country_related_render_values(kw, render_values))
        return request.render("website_sale.address", render_values)
