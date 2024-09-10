# -*- coding: utf-8 -*-
#################################################################################
# Author      : Xrero Software Pvt. Ltd. (<https://Xrero.com/>)
# Copyright(c): 2015-Present Xrero Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.Xrero.com/license.html/>
#################################################################################
{
  "name"                 :  "Xrero SaaS Custom Plans",
  "summary"              :  """Odoo SaaS Custom Plans allows you to provide option to your clients to select custom Plans of their choice for Xrero Saas Kit""",
  "category"             :  "Extra Tools",
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "Xrero Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.Xrero.com/",
  "description"          :  """Provide Custom plan option for Xrero saas Kit.""",
  "live_test_url"        :  "http://odoodemo.Xrero.com/demo_feedback?module=saas_kit_custom_plans",
  "depends"              :  [
                             'odoo_saas_kit',
                            ],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'wizards/disable_odoo_version_wizard_view.xml',
                             'wizards/cancel_odoo_version_wizard_view.xml',
                             'views/saas_client.xml',
                             'views/product_view.xml',
                             'views/product_page.xml',
                             'views/odoo_version_view.xml',
                             'views/saas_module.xml',
                             'views/res_config_view.xml',
                             'data/request_sequence.xml',
                             'data/contract_expiry_warning_template.xml',
                             'views/plan_view.xml',
                             'views/contract_view.xml',
                             'views/menuitems.xml',
                             'views/page_template.xml',
                             'views/portal_template.xml',
                             'data/product.xml',
                             'data/module_installation_crone.xml',
                             'data/contract_expiry_warning_mail_crone.xml'
                            ],
  "assets"               : {
                            "web.assets_frontend": [
                              '/saas_kit_custom_plans/static/src/js/custom_plan.js',
                              '/saas_kit_custom_plans/static/src/js/update_app.js',
                              '/saas_kit_custom_plans/static/src/css/custom_plan_apps_page.css',
                            ]
                           },
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
