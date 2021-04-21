# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

from odoo import fields, models
import requests, json
from odoo.exceptions import UserError


class JdySettlementType(models.Model):
    _name = "jdy.settlement.type"
    _description = "JDY结算方式"

    jdy_id = fields.Char(u"结算方式id")
    name = fields.Char(u"结算方式名称")
    enable = fields.Char(u"是否可用")
    is_default = fields.Boolean(u"是否默认")

    def sync_jdy_settlement_type(self):
        # 给出返回action
        action = self.env.ref('base_setup.action_general_configuration').read()[0]
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        type_obj = self.env['jdy.settlement.type'].sudo()
        # 取得全部结算方式
        type_list = requests.post('http://api.kingdee.com/jdy/basedata/settlement_type_list',
                                  params=params, headers=headers, verify=False)
        if not type_list.json().get('success'):
            raise UserError(u'获取支结算方式失败')
        # 保存结算方式
        for settlement in type_list.json().get('data').get('rows'):
            data = {
                'jdy_id': settlement.get('id'),
                'enable': settlement.get('enable'),
                'name': settlement.get('name'),
                'is_default': settlement.get('isdefault')
            }
            settlement_type = type_obj.search([('jdy_id', '=', settlement.get('id'))])
            if len(settlement_type) == 0:
                type_obj.create(data)
            else:
                settlement_type.write(data)
        return action
