# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    You should have received a copy of the License along with this program.
#    If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import models, fields, api
from odoo.exceptions import UserError


CYCLE = [
    ('half_day', 'Twice a day'),
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('yearly', 'Yearly'),
]



class CreateBackupProcess(models.TransientModel):
    _name = 'backup.process.wizard'
    
    
    name = fields.Char(string="Name")
    frequency = fields.Integer(string="Frequency", default=1)
    frequency_cycle = fields.Selection(selection=CYCLE, string="Backup Frequency", default='hour')
    storage_path = fields.Char(string="Storage Path")
    backup_starting_time = fields.Datetime(string="Backup Starting Date and Time")


    def create_process_data(self):
        client_id = self._context['client_id']
        client_id = self.env['saas.client'].sudo().browse([client_id])
        if self.frequency_cycle == 'half_day':
            frequency = 2
        else:
            frequency = 1
        client_id.create_backup_process(frequency=frequency, frequency_cycle=self.frequency_cycle, backup_starting_time=self.backup_starting_time)


class CancelBackupPrcoessWizard(models.TransientModel):
    _name = 'cancel.backup.process'


    name = fields.Char(string="Name")
    purpose = fields.Selection(selection=[('cancel_backup', 'Cancel Backup')], string="Purpose")
    record_id = fields.Integer(string="Record Id")


    def call_record_method(self):
        res = self.env['saas.client'].sudo().search([('id', '=', self.record_id)])
        res.delete_backup_crone()
