# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

from odoo import fields, models, api
import requests, json
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    jdy_id = fields.Char(u"精斗云id", copy=False)
    jdy_sync = fields.Boolean(u"是否与精斗云已同步", copy=False)

    def sync_jdy_account(self):
        # 给出返回action
        action = self.env.ref('base_setup.action_general_configuration').read()[0]
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        # 取得全部分组
        raw = requests.post('http://api.kingdee.com/jdy/gl/voucher_type_list',
                            params=params, headers=headers, verify=False)
        if not raw.json().get('success'):
            raise UserError(u'获取凭证字列表失败')
        journals = raw.json().get('data').get('rows')
        journal_obj = self.env['account.journal'].sudo()
        for item in journals:
            journal = journal_obj.search([('code', '=', item.get('name'))])
            data = {
                'jdy_id': item.get('id'),
                'jdy_sync': True
            }
            if len(journal) == 0:
                data['type'] = 'general'
                data['name'] = item.get('name')
                data['code'] = item.get('name')
                journal.create(data)
            else:
                journal.write(data)
        return action
