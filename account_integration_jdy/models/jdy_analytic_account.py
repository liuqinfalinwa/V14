# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

from odoo import fields, models
import requests, json
from odoo.exceptions import UserError


class JdyAnalyticAccount(models.Model):
    _name = "jdy.analytic.account"
    _description = "JDY分析科目"

    jdy_id = fields.Char(u"精斗云id")
    name = fields.Char(u"辅助核算科目名称")
    number = fields.Char(u"辅助核算科目编码")
    enable = fields.Char(u"状态(1-可用, 0-不可用)")
    group_id = fields.Char(u'自定义类别id')
    group_number = fields.Char(u'自定义类别number')
    group_name = fields.Char(u'自定义类别name')
    group_parent_id = fields.Char(u"上级类别jdy id")

    def sync_jdy_analytic_account(self):
        # 给出返回action
        action = self.env.ref('base_setup.action_general_configuration').read()[0]
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        # 取得全部分组
        raw = requests.post('http://api.kingdee.com/jdy/basedata/auxinfotype_list',
                            params=params, data=json.dumps({'pagesize': 100}), headers=headers, verify=False)
        if not raw.json().get('success'):
            raise UserError(u'获取辅助核算项分组失败')
        groups = {}
        for group in raw.json().get('data').get('rows'):
            groups[group.get('id')] = group
        # 取得全部辅助核算项，并处理精斗云分页
        page = 1
        while True:
            aux = requests.post('http://api.kingdee.com/jdy/basedata/auxinfo_list',
                                params=params, data=json.dumps({'page': page, 'pagesize': 100}),
                                headers=headers, verify=False)
            if not raw.json().get('success'):
                raise UserError(u'获取辅助核算项失败')
            auxinfo = aux.json().get('data').get('rows')
            jdy_obj = self.env['jdy.analytic.account'].sudo()
            for item in auxinfo:
                analytic = jdy_obj.search([('jdy_id', '=', item.get('id'))])
                data = {
                    'jdy_id': item.get('id'),
                    'name': item.get('name'),
                    'number': item.get('number'),
                    'enable': item.get('enable'),
                    'group_id': item.get('group'),
                    'group_number': groups.get(item.get('group')).get('number'),
                    'group_name': groups.get(item.get('group')).get('name'),
                    'group_parent_id': groups.get(item.get('group')).get('parent_id')
                }
                # 每次全部更新，存在的辅助核算科目则进行更新
                if len(analytic) == 0:
                    jdy_obj.create(data)
                else:
                    analytic.write(data)
            if aux.json().get('data').get('totalpage') == page:
                break
            else:
                page += 1
        return action
