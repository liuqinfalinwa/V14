# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

from odoo import fields, models, api
import requests, json
from odoo.exceptions import UserError
from datetime import datetime


class AccountMove(models.Model):
    _inherit = "account.move"

    jdy_id = fields.Char("JDY单据id", copy=False)
    jdy_sync = fields.Boolean(u"是否与精斗云已同步", copy=False)
    jdy_bill_no = fields.Char(u"JDY单据编号", copy=False)
    jdy_journal_sync = fields.Boolean(u"账簿是否与精斗云已同步", related="journal_id.jdy_sync", readonly=True)
    jdy_income_type = fields.Many2one("jdy.voucher.type", string="JDY应收类别", domain=[('voucher_type', '=', 'income')], copy=False)
    jdy_pay_type = fields.Many2one("jdy.voucher.type", string="JDY应付类别", domain=[('voucher_type', '=', 'pay')], copy=False)

    def sync_account_move_to_jdy(self):
        # 给出返回action
        form_view = self.env.ref('account.view_move_form')
        action = {
            'name': u"分录",
            'res_model': 'account.move',
            'res_id': self.id,
            'views': [(form_view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'inline'
        }
        am_list = self
        if len(self) == 0:
            journal_ids = self.env['account.journal'].search([('jdy_sync', '=', True)])
            am_list = self.env['account.move'].search([('jdy_sync', '=', False), ('journal_id', 'in', journal_ids.ids)])
            action = self.env.ref('base_setup.action_general_configuration').read()[0]
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        items = []
        for am in am_list:
            if not am.journal_id.jdy_sync:
                raise UserError(u"账簿尚未与精斗云同步，无法上传分录，相关分录："+am.name)
            if am.jdy_sync:
                raise UserError(u"分录已上传过，无法重复上传："+am.name)
            data = {
                'date': datetime.strftime(am.date, "%Y-%m-%d"),
                'groupid_id': am.journal_id.jdy_id,
                'remark': am.narration or ' '
            }
            entries = []
            for line in am.line_ids:
                analytics = []
                if line.partner_id.jdy_customer_sync:
                    analytics.append({'type': 'bd_customer', 'id': line.partner_id.jdy_customer_id})
                if line.partner_id.jdy_supplier_sync:
                    analytics.append({'type': 'bd_supplier', 'id': line.partner_id.jdy_supplier_id})
                if line.jdy_analytic_dept:
                    analytics.append({'type': 'bd_department', 'id': line.jdy_analytic_dept.jdy_id})
                if line.jdy_analytic_emp:
                    analytics.append({'type': 'bd_employee', 'id': line.jdy_analytic_emp.jdy_id})
                if line.jdy_analytic_other:
                    analytics.append({
                        'type': 'bd_auxinfo',
                        'bd_auxinfo_type_id': line.jdy_analytic_other.group_id,
                        'id': line.jdy_analytic_other.jdy_id
                    })
                entries.append({
                    'dc': line.account_id.jdy_dc,
                    'explanation': am.ref,
                    'debitamount': line.debit,
                    'creditamount': line.credit,
                    'account_id': line.account_id.jdy_id,
                    'assist': analytics
                })
            data['entries'] = entries
            items.append(data)
        # 保存凭证到精斗云
        if len(items) > 0:
            raw = requests.post('http://api.kingdee.com/jdy/gl/voucher_save',
                                params=params, data=json.dumps({'items': items}), headers=headers, verify=False)
            if not raw.json().get('success'):
                raise UserError(u'凭证写入精斗云失败，错误为：' + raw.json().get('description_cn', ' ') +
                                raw.json().get('message', ' '))
            try:
                if not raw.json().get('data')[0].get('success'):
                    raise UserError(raw.json().get('data')[0].get('errorInfo', ' ')[0].get('msg'))
            except Exception:
                raise UserError(raw.json().get('data'))
            jdy_id = raw.json().get('data')[0].get('successPkIds')[0]
            am_list.write({
                'jdy_bill_no': jdy_id,
                'jdy_sync': True
            })
        return action

    def sync_invoice_to_jdy(self):
        return self.sync_invoice_bill_to_jdy("ar")

    def sync_bill_to_jdy(self):
        return self.sync_invoice_bill_to_jdy("ap")

    def sync_invoice_bill_to_jdy(self, invoice_type):
        # 给出返回action
        form_view = self.env.ref('account.view_move_form')
        action = {
            'name': u"发票",
            'res_model': 'account.move',
            'res_id': self.id,
            'views': [(form_view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'inline'
        }
        am_list = self
        if invoice_type == 'ar':
            domain = [('jdy_sync', '=', False), ('move_type', 'in', ['out_invoice', 'out_refund', 'out_receipt'])]
            url = 'http://api.kingdee.com/jdy/arap/ar_other_credit_save'
            detail_url = 'http://api.kingdee.com/jdy/arap/ar_other_credit_detail'
        elif invoice_type == "ap":
            domain = [('jdy_sync', '=', False), ('move_type', 'in', ['in_invoice', 'in_refund', 'in_receipt'])]
            url = 'http://api.kingdee.com/jdy/arap/ap_other_credit_save'
            detail_url = 'http://api.kingdee.com/jdy/arap/ap_other_credit_detail'
        else:
            raise UserError("传入的参数错误")
        if len(self) == 0:
            journal_ids = self.env['account.journal'].search([('jdy_sync', '=', True)])
            am_list = self.env['account.move'].search(domain)
            action = self.env.ref('base_setup.action_general_configuration').read()[0]
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        for am in am_list:
            # TODO Check Analytic Account Correction.
            if am.amount_total == 0:
                raise UserError(u"发票金额不能为0，涉及发票为：" + am.name)
            if invoice_type == "ar":
                if am.move_type not in ['out_invoice', 'out_refund', 'out_receipt']:
                    raise UserError(u"非客户发票无法上传至精斗云其他应收，涉及发票为：" + am.name)
                if not am.partner_id.jdy_customer_sync:
                    raise UserError(u"发票客户没有与精斗云同步，无法上传，涉及发票为：" + am.name)
                if not am.jdy_income_type:
                    raise UserError(u"发票未设定JDY其他应收类别，请先设定发票的应收类型，涉及发票为：" + am.name)
            if invoice_type == "ap":
                if am.move_type not in ['in_invoice', 'in_refund', 'in_receipt']:
                    raise UserError(u"非供应商账单无法上传至精斗云其他应付，涉及账单为：" + am.name)
                if not am.partner_id.jdy_supplier_sync:
                    raise UserError(u"账单供应商没有与精斗云同步，无法上传，涉及账单为：" + am.name)
                if not am.jdy_pay_type:
                    raise UserError(u"账单未设定JDY其他应付类别，请先设定账单的应付类型，涉及账单为：" + am.name)
            if am.state != 'posted':
                raise UserError(u"状态不为已审核，涉及Invoice为：" + am.name)
            if len(am.partner_id) == 0:
                raise UserError(u"没有Partner时无法上传，涉及Invoice为：" + am.name)
            if am.jdy_sync:
                raise UserError(u"Invoice已上传，无法重复上传Invoice，涉及Invoice为：" + am.name)
            data = {
                'billsource': "APP",
                'billdate': datetime.strftime(am.invoice_date, "%Y-%m-%d"),
                'biztype': "1",
                'itemclass_id': am.partner_id.jdy_customer_id if invoice_type == "ar" else am.partner_id.jdy_supplier_id,
                'remark': am.narration or ' ',
                'payfromtoentry': [{
                    'paccttype_id': am.jdy_income_type.jdy_id if invoice_type == "ar" else am.jdy_pay_type.jdy_id,
                    'amount': am.amount_total,
                    'comment': am.name or ' '
                }]
            }

            if invoice_type == "ar" and am.invoice_user_id.employee_id.jdy_id:
                data['emp_id'] = am.invoice_user_id.employee_id.jdy_id
            # 保存发票到精斗云
            raw = requests.post(url, params=params, data=json.dumps(data), headers=headers, verify=False)
            if not raw.json().get('success'):
                raise UserError(u'写入精斗云失败，错误为：' + raw.json().get('description_cn', ' ') +
                                raw.json().get('message', ' '))
            # 取得jdy返回的id
            if not raw.json().get('data').get('success'):
                raise UserError(raw.json().get('data').get('message'))
            jdy_id = raw.json().get('data').get('successPkIds')[0]
            try:
                raw_ar = requests.post(detail_url, params=params,
                                   data=json.dumps({'id': jdy_id}), headers=headers, verify=False)
                bill_no = raw_ar.json().get('data').get('billno')
            except Exception as e:
                bill_no = "取得JDY编号失败"
            # 将精斗云的id与编码记录在odoo的发票中
            am.write({
                'jdy_id': jdy_id,
                'jdy_bill_no': bill_no,
                'jdy_sync': True
            })
        return action

