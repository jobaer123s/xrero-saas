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
  "name"                 :  "Saas Kit Backup",
  "summary"              :  """Module provide feature to saas clients to take backups of client instance's database and later download them.""",
  "category"             :  "Extra Tools",
  "version"              :  "1.0.0",
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/",
  "description"          :  """Module provide feature to saas clients to take backups of client instance's database and later download them.""",
  "live_test_url"        :  "http://odoodemo.webkul.com/demo_feedback?module=saas_kit_backup",
  "depends"              :  [
                             'odoo_saas_kit',
                             'wk_backup_restore',
                            ],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'wizard/backup_process_wizard.xml',
                             'views/saas_client_view.xml',
                             'views/saas_server_view.xml',
                             #'views/backup_process.xml',
                             'views/backup_template.xml',
                             'views/contract_portal_page.xml',
                            ],
  "assets"               : {
                              'web.assets_frontend': [
                                '/saas_kit_backup/static/src/js/backup_process.js',
                                '/saas_kit_backup/static/src/css/backup_process.css'
                              ]
                            },
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
