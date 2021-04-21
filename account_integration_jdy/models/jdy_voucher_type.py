# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

from odoo import fields, models
import requests, json
from odoo.exceptions import UserError


class JdyVoucherType(models.Model):
    _name = "jdy.voucher.type"
    _description = "JDY其他应收应付类型"

    jdy_id = fields.Char(u"支出类型id")
    name = fields.Char(u"类型名称")
    number = fields.Char(u"类型编码")
    voucher_type = fields.Selection([('pay', u'支出'), ('income', u'收入')], string=u"类别定义")

    def sync_jdy_voucher_type(self):
        # 给出返回action
        action = self.env.ref('base_setup.action_general_configuration').read()[0]
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        type_obj = self.env['jdy.voucher.type'].sudo()
        # 取得全部支出类别
        pay_list = requests.post('http://api.kingdee.com/jdy/basedata/pay_out_type_list',
                                 params=params, headers=headers, verify=False)
        if not pay_list.json().get('success'):
            raise UserError(u'获取支出类别失败')
        # 保存支出类别
        for pay in pay_list.json().get('data').get('rows'):
            data = {
                'jdy_id': pay.get('id'),
                'number': pay.get('number'),
                'name': pay.get('name'),
                'voucher_type': 'pay'
            }
            pay_type = type_obj.search([('jdy_id', '=', pay.get('id')), ('voucher_type', '=', 'pay')])
            if len(pay_type) == 0:
                type_obj.create(data)
            else:
                pay_type.write(data)

        # 取得全部收入类别
        income_list = requests.post('http://api.kingdee.com/jdy/basedata/paccttype_list',
                                    params=params, headers=headers, verify=False)
        if not income_list.json().get('success'):
            raise UserError(u'获取其他收入类别失败')
        # 保存收入类别
        for income in income_list.json().get('data').get('rows'):
            data = {
                'jdy_id': income.get('id'),
                'number': income.get('number'),
                'name': income.get('name'),
                'voucher_type': 'income'
            }
            income_type = type_obj.search([('jdy_id', '=', pay.get('id')), ('voucher_type', '=', 'income')])
            if len(income_type) == 0:
                type_obj.create(data)
            else:
                income_type.write(data)
        return action
