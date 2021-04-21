# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

from odoo import fields, models
import requests, json
from odoo.exceptions import UserError


class JdySettlementAccount(models.Model):
    _name = "jdy.settlement.account"
    _description = "JDY结算账户"

    jdy_id = fields.Char(u"结算账户id")
    number = fields.Char(u"结算账户编码")
    name = fields.Char(u"结算账户名称")
    account_name = fields.Char(u"开户名")
    bank = fields.Char(u"开户行")
    account = fields.Char(u"卡号")
    enable = fields.Char(u"是否可用")
    is_default = fields.Boolean(u"是否默认")

    def sync_jdy_settlement_account(self):
        # 给出返回action
        action = self.env.ref('base_setup.action_general_configuration').read()[0]
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        account_obj = self.env['jdy.settlement.account'].sudo()
        # 取得全部结算账户
        account_list = requests.post('http://api.kingdee.com/jdy/basedata/settlement_account_list',
                                     params=params, headers=headers, verify=False)
        if not account_list.json().get('success'):
            raise UserError(u'获取支结算账户失败')
        # 保存结算账户
        for account in account_list.json().get('data').get('rows'):
            data = {
                'jdy_id': account.get('id'),
                'number': account.get('number'),
                'name': account.get('name'),
                'account_name': account.get('accountname'),
                'enable': account.get('enable'),
                'bank': account.get('openingbank'),
                'account': account.get('account'),
                'is_default': account.get('isdefault')
            }
            settlement_account = account_obj.search([('jdy_id', '=', account.get('id'))])
            if len(settlement_account) == 0:
                account_obj.create(data)
            else:
                settlement_account.write(data)
        return action
