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
  "name"                 :  "Saas Tool",
  "summary"              :  "Saas Tool",
  "category"             :  "Extra",
  "version"              :  "1.0.1",
  "sequence"             :  1,
  "author"               :  "Xrero Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "description"          :  """Saas tools""",
  "depends"              :  [
                                'base', 'web', 'mail'
                            ],
  "data"                  : [
                              'data/ir_config_parameter.xml',
                            ],
  'assets'               : {
                             'web.assets_backend': [
                               "wk_saas_tool/static/src/css/trial_information.css",
                              "wk_saas_tool/static/src/js/trial_information.js"
                            ],
    
    },
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  True,
}
