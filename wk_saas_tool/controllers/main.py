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

from werkzeug.exceptions import BadRequest
from odoo.http import request
from odoo import http
from odoo.addons.web.controllers.main import Home
import logging

_logger = logging.getLogger(__name__)


class SaaSLogin(http.Controller):

    
    @http.route('/saas/login', type='http', auth='public', website=True)
    def autologin(self, **kw):
        """login user via Odoo Account provider
        QUERY : SELECT COALESCE(password, '') FROM res_users WHERE id=1;
        import base64
        base64.b64encode(s.encode('utf-8'))
        """
        db = request.params.get('db') and request.params.get('db').strip()
        dbname = kw.pop('db', None)
        redirect_url = kw.pop('redirect_url', '/web')
        login = kw.pop('login', 'admin')
        password = kw.pop('passwd', None)
        if not dbname:
            return BadRequest()
        uid = request.session.authenticate(dbname, login, password)
        request.params['login_success'] = True

        return http.request.redirect(redirect_url)

       