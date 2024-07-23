# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    You should have received a copy of the License along with this program.
#    If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError
from odoo.modules.module import get_module_resource
from datetime import datetime
import base64
from pytz import timezone
import pytz


import configparser
import logging

_logger = logging.getLogger(__name__)


BACKUP_STATE = [
    ('draft', 'Draft'),
    ('confirm', 'Confirm'),
    ('running', 'Running'),
    ('cancel', 'Cancel')
]

class SaasClientBackup(models.Model):
    _inherit = 'saas.client'

    backup_process_id = fields.Many2one(comodel_name='backup.process', string="Backup Process")
    is_crone_ignited = fields.Boolean(string="Backup Attaches", default=False)
    crone_state = fields.Selection(selection=BACKUP_STATE, related='backup_process_id.state', string="Crone state")


    def get_backup(self):
        config = configparser.RawConfigParser()
        module_path = get_module_resource('odoo_saas_kit')
        config.read(module_path+'/models/lib/saas.conf')
        config_dict = dict(config.items('options'))
        _logger.info("-------- called from client---------")
        db_user = self.server_id.db_user
        db_password = self.server_id.db_pass
        url = 'localhost' if self.server_id.host_server == 'self' else self.server_id.sftp_host
        url += ':'+self.containter_port
        res = self.backup_process_id.call_backup_script(master_pass=config_dict['container_master'], port_number=self.containter_port, url=url, db_user=db_user, db_password=db_password)
        if res.get('success'):
            self.is_crone_ignited = True

    def create_backup_process(self, frequency=1, frequency_cycle=None, backup_starting_time=None):
        """
        Call from wizard and will to create/update the backup process.
        """
        user_time_zone = self.saas_contract_id.partner_id.tz or self._context.get('tz')
        local_zone = pytz.timezone(user_time_zone)
        if type(backup_starting_time) == str:
            naive_datetime = datetime.strptime(backup_starting_time, "%Y-%m-%d %H:%M")
            local_datetime = local_zone.localize(naive_datetime, is_dst=None)
        else:
            local_datetime = local_zone.localize(backup_starting_time, is_dst=None)
        utc_datetime = local_datetime.astimezone(pytz.utc)
        backup_starting_time = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
        vals = dict(
            frequency=frequency,
            frequency_cycle=frequency_cycle,
            storage_path=self.containter_path,
            backup_location=self.server_id.backup_location,
            db_name=self.database_name,
            saas_client_id=self.id,
            backup_starting_time=backup_starting_time,
        )
        if self.backup_process_id and not self.backup_process_id.state == 'cancel':
            vals['update_requested'] = True
            self.backup_process_id.write(vals)
        else:
            backup_record = self.env['backup.process'].sudo().create(vals)
            self.backup_process_id = backup_record.id


    def update_backup_process(self):
        """
        Call from client record and will pop up a wizard for update params.
        """
        vals = dict(
            name='update',
            frequency=self.backup_process_id.frequency,
            frequency_cycle=self.backup_process_id.frequency_cycle,
            backup_starting_time=self.backup_process_id.backup_starting_time
        )
        res = self.env['backup.process.wizard'].sudo().create(vals)
        return {
            'name': _('Update Backup Process'),
            'res_model': 'backup.process.wizard',
            'view_mode': 'form',
            'res_id' : res.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'client_id': self.id}
        }

    def cancel_backup_process(self):
        """
        Call from client record and will pop up a wizard for confirmation.
        """
        vals = dict(
            name='Are you sure you want to Cancel/Delete the attach Backup Prcoess. It will stop the future backups ?',
            purpose='cancel_backup',
            record_id=self.id,
        )
        res = self.env['cancel.backup.process'].sudo().create(vals)
        return {
            'name': _('Confirmation'),
            'res_model': 'cancel.backup.process',
            'view_mode': 'form',
            'res_id' : res.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def delete_backup_crone(self):
        """
        Call from wizard to delete the crone.
        """
        res = self.backup_process_id.remove_attached_cron()
        _logger.info('-----  %r -------'%res)        
        if res.get('success'):
            self.is_crone_ignited = False


    @api.model
    def get_create_backup_process_data(self, frequency, frequency_cycle, starting_date, update_req, client_id):
        """
        Called from JS to Create/Update process.
        Upate Req args is for future purpose.
        """
        client_id = self.env['saas.client'].sudo().browse([client_id])
        starting_date = starting_date.replace('T', ' ')
        client_id.create_backup_process(frequency=int(frequency), frequency_cycle=frequency_cycle, backup_starting_time=starting_date)
        data = dict()
        data['contract_id'] = client_id.saas_contract_id.id
        data['token'] = client_id.saas_contract_id.token
        return data

    def get_cancel_backup_process_call(self, client_id):
        """
        Call from JS to Cancel the process
        """
        client_id = self.env['saas.client'].sudo().browse([client_id])
        client_id.delete_backup_crone()
        data = dict()
        data['contract_id'] = client_id.saas_contract_id.id
        data['token'] = client_id.saas_contract_id.token
        return data

    def download_backup_process(self, detail_id=None):
        file_path = detail_id.file_path + detail_id.file_name
        result = None
        with open(file_path , 'rb') as reader:
            result = base64.b64encode(reader.read())
        attachment_obj = self.env['ir.attachment'].sudo()
        name = detail_id.file_name
        attachment_id = attachment_obj.create({
            'name': name,
            'datas': result,
            'public': True
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
        return download_url
    
    def get_download_backup_zip_call(self, client_id, detail_id, name):
        """
        Call from JS to call download function
        """
        client_id = self.env['saas.client'].sudo().browse([client_id])
        detail_id = self.env['backup.process.detail'].sudo().browse([detail_id])
        if detail_id in client_id.backup_process_id.backup_details_ids and detail_id.name == name:
            return client_id.download_backup_process(detail_id=detail_id)
        else:
            return False            

