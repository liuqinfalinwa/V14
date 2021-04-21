# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

from odoo import fields, models
import requests, json
from odoo.exceptions import UserError


class AccountAccount(models.Model):
    _inherit = "account.account"

    jdy_id = fields.Char(u"精斗云id")
    jdy_parent_id = fields.Char(u"上级科目id", copy=False)
    jdy_level = fields.Integer(u"科目级次", copy=False)
    jdy_accounttype_id = fields.Char(u"科目类别id", copy=False)
    jdy_accounttype_name = fields.Char(u"科目类别名称", copy=False)
    jdy_accounttype_number = fields.Char(u"科目类别编码", copy=False)
    jdy_dc = fields.Integer(u"余额方向，借/贷 （借方科目：1；贷方科目:-1）", copy=False)
    jdy_help_code = fields.Char(u"助记码", copy=False)
    jdy_isbank = fields.Boolean(u"是否银行科目", copy=False)
    jdy_iscash = fields.Boolean(u"是否现金科目", copy=False)
    jdy_iscashequivalent = fields.Boolean(u"是否现金等价物", copy=False)
    jdy_currencies = fields.Char(u"货币代码", copy=False)
    jdy_isqty = fields.Boolean(u"是否数量核算", copy=False)
    jdy_iscurrency = fields.Boolean(u"是否外币核算", copy=False)
    jdy_rdbtnall = fields.Boolean(u"是否所有币别", copy=False)
    jdy_ischangecurrency = fields.Boolean(u"是否期末调汇", copy=False)
    jdy_isassist = fields.Boolean(u"是否辅助核算项", copy=False)
    jdy_sync = fields.Boolean(u"是否与精斗云已同步", copy=False)
    jdy_enable = fields.Char(u"是否启用", copy=False)

    def get_account_from_jdy(self):
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        raw = requests.post('http://api.kingdee.com/jdy/gl/account_list',
                            params=params, headers=headers, verify=False)
        if not raw.json().get('success'):
            raise UserError(u'获取科目失败，请联系管理员检查精斗云账号设定及权限，错误代码为'+raw.json().get('errorCode', ' '))
        account_obj = self.env['account.account']
        i = 0
        for account in raw.json().get('data').get('items'):
            acc_raw = requests.post('http://api.kingdee.com/jdy/gl/account_detail',
                                    params=params, headers=headers, data=json.dumps({'id': account.get('id')}),
                                    verify=False)
            acc = acc_raw.json().get('data')
            data = {
                'code': acc.get('number'),
                'name': acc.get('name'),
                'user_type_id': self._get_type_id(acc.get('accounttype_name')),
                'jdy_id': acc.get('id', ''),
                'jdy_parent_id': acc.get('parent_id', ''),
                'jdy_level': acc.get('level', ''),
                'jdy_accounttype_id': acc.get('accounttype_id', ''),
                'jdy_accounttype_name': acc.get('accounttype_name', ''),
                'jdy_accounttype_number': acc.get('accounttype_number', ''),
                'jdy_dc': acc.get('dc', ''),
                'jdy_help_code': acc.get('helpcode'),
                'jdy_isbank': acc.get('isbank', False),
                'jdy_currencies': acc.get('currencys'),
                'jdy_iscash': acc.get('iscash', False),
                'jdy_iscashequivalent': acc.get('iscashequivalent', False),
                'jdy_isqty': acc.get('isqty', False),
                'jdy_iscurrency': acc.get('iscurrency', False),
                'jdy_rdbtnall': acc.get('rdbtnall', False),
                'jdy_ischangecurrency': acc.get('ischangecurrency', False),
                'jdy_enable': acc.get('enable'),
                'jdy_isassist': acc.get('isassist', False),
                'jdy_sync': True
            }
            odoo_acc = account_obj.search([('code', '=', account.get('number'))])
            if len(odoo_acc) == 0:
                odoo_acc = account_obj.create(data)
            else:
                odoo_acc.write(data)
            # 把科目与分析科目对应关系写入
            # jdy_ids = []
            # for analytic in acc.get('checkitementry'):
            #     if analytic.get('type') == 'bd_auxinfo':
            #         jdy_ids.append(analytic.get('bd_auxinfo_type_id'))
            # ids_analytics = self.env['jdy.analytic.account'].search([('jdy_id', 'in', [jdy_ids])])
            # if len(ids_analytics) > 0:
            #     odoo_acc.write({'jdy_analytic_ids': (6, 0, ids_analytics.ids)})

    def _get_type_id(self, categ_name):
        model = self.env['ir.model.data']
        account_type = {
            'current_asset': model.xmlid_to_res_id('account.data_account_type_current_assets'),
            'non-current_asset': model.xmlid_to_res_id('account.data_account_type_non_current_assets'),
            'current_liability': model.xmlid_to_res_id('account.data_account_type_current_liabilities'),
            'non-current_liability': model.xmlid_to_res_id('account.data_account_type_non_current_liabilities'),
            'equity': model.xmlid_to_res_id('account.data_account_type_equity'),
            'cost': model.xmlid_to_res_id('account.data_account_type_direct_costs'),
            'income': model.xmlid_to_res_id('account.data_account_type_revenue'),
            'other_income': model.xmlid_to_res_id('account.data_account_type_other_income'),
            'expense': model.xmlid_to_res_id('account.data_account_type_expenses'),
            'unaffected_earning': model.xmlid_to_res_id('account.data_unaffected_earnings')
        }
        type_name = ''
        if categ_name == '流动资产':
            type_name = 'current_asset'
        if categ_name == '非流动资产':
            type_name = 'non-current_asset'
        if categ_name == '流动负债':
            type_name = 'current_liability'
        if categ_name == '非流动负债':
            type_name = 'non-current_liability'
        if categ_name == '所有者权益':
            type_name = 'equity'
        if categ_name == '营业收入':
            type_name = 'income'
        if categ_name == '其他收益':
            type_name = 'other_income'
        if categ_name in ['期间费用', '其他损失']:
            type_name = 'expense'
        if categ_name in ['营业成本及税金', '所得税', '成本']:
            type_name = 'cost'
        if categ_name == '以前年度损益调整':
            type_name = 'unaffected_earning'
        if type_name == '':
            raise UserError(u'精斗云有更新科目类型，请通知作者更新代码表')
        return account_type.get(type_name)
