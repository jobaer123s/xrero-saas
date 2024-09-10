# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Xrero Software Pvt. Ltd. (<https://Xrero.com/>)
#    You should have received a copy of the License along with this program.
#    If not, see <https://store.Xrero.com/license.html/>
#################################################################################

from . import models
from . import wizard
from . import controllers

def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import UserError
    version_info = common.exp_version()
    server_serie =version_info.get('server_serie')
    if server_serie != '17.0':
        raise UserError('Module support Odoo series 17.0 found {}.'.format(server_serie))
    return True
