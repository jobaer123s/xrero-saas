# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "SaaS Kit Trial",
  "summary"              :  """The module allows you to provides free trial of Odoo instance to a particular Client""",
  "category"             :  "Extra Tools",
  "version"              :  "1.0.0",
  "sequence"             :  2,

  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/",
  "description"          :  """The module allows you to provides free trial of Odoo instance to a particular Client""",
  "live_test_url"        :  "http://odoodemo.webkul.com/demo_feedback",
  "depends"              :  ['odoo_saas_kit'],
  "data"                 :  [
                             'views/trial_plan_view.xml',
                             'views/saas_trial_contract.xml',
                             'views/res_config.xml',
                             'views/portal_template.xml',
                             'views/trial_product.xml',
                             'data/trial_email_template.xml',
                             'data/trial_expiry_cron.xml',
                             'data/product_data.xml'
                            ],
  "assets"               : {
                             'web.assets_frontend': [
                               '/saas_kit_trial/static/src/js/saas_trial.js',
                               '/saas_kit_trial/static/src/js/saas_trial_contract_portal.js'
                              ],

                              'web.assets_backend':[
                               '/saas_kit_trial/static/src/css/saas_trial_contract.css'  
                              ]
                           },
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
