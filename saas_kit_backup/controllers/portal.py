# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import http, _
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import consteq
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager

import logging

_logger = logging.getLogger(__name__)

class BackupPortal(CustomerPortal):
    
    @http.route(['/my/backup/files/<int:contract>', '/my/backup/files/page/<int:page>'], type='http', auth="user", website=True)
    def render_my_backups(self, page=1, contract=None, access_token=None, **kw):
        try :
            _logger.info("==========  %r =========="%contract)
            _logger.info("==========  %r =========="%access_token)
            if not contract or not access_token:
                raise AccessError("Missing Token")
            contract_sudo = self._contract_check_access(contract, access_token)
        except AccessError:
            return request.redirect('/my')
        values = self._contract_get_page_view_values(contract_sudo, access_token, **kw)        
        # values = self._prepare_portal_layout_values()
        backup_process = contract_sudo.saas_client.backup_process_id
        pager = portal_pager(
            url="/my/backup/files",
            # url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=len(backup_process.backup_details_ids),
            page=page,
            step=10
        )
        values.update({
            'pager': pager,
            'backup_process': backup_process,
            'contract_id' : contract_sudo,
        })
        _logger.info("------------ Yes  %r------------"%contract_sudo)
        return request.render('saas_kit_backup.my_backup_page', values)
