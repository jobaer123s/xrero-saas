# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Xrero Software Pvt. Ltd. (<https://Xrero.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.Xrero.com/license.html/>
# 
#################################################################################

from . import models
from . import wizards
from . import controllers

def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import UserError
    version_info = common.exp_version()
    server_serie = version_info.get('server_serie')
    if server_serie != '17.0':
        raise UserError(
           'Module support Xrero series 17.0 found {}.'.format(server_serie))
    return True
