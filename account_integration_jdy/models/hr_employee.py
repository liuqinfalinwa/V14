# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

from odoo import fields, models, api
import requests, json
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    jdy_id = fields.Char(u"精斗云id", copy=False)
    jdy_number = fields.Char(u'精斗云员工编码', copy=False)
    jdy_sync = fields.Boolean(u"是否与精斗云已同步", copy=False)

    @api.model
    def create(self, vals):
        res = super(HrEmployee, self).create(vals)
        if self._context.get('tracking_disable'):
            return res
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        data = {
            'name': res.name,
            'number': 'V14-' + str(res.id),
            'gender': '1' if res.gender == 'male' else '0',
            'mobile': res.mobile_phone or '',
            'email': res.work_email or '',
            'idnumber': res.identification_id or ''
        }
        # 保存员工到精斗云
        raw = requests.post('http://api.kingdee.com/jdy/basedata/emp_save',
                            params=params, data=json.dumps(data), headers=headers, verify=False)
        if not raw.json().get('success'):
            raise UserError(u'员工写入精斗云失败，错误为：' + raw.json().get('description_cn', ' ') +
                            raw.json().get('message', ' '))
        # 取得jdy返回的员工id
        jdy_emp_id = raw.json().get('data').get('successPkIds')[0]
        # 将精斗云的员工id与编码记录在odoo的部门中
        res.write({
            'jdy_id': jdy_emp_id,
            'jdy_number': 'V14-' + str(res.id),
            'jdy_sync': True
        })
        return res

    def sync_emp_to_jdy(self):
        # 给出返回action
        action = self.env.ref('hr.open_view_employee_list_my').read()[0]
        emp_list = self
        if len(self) == 0:
            emp_list = self.env['hr.employee'].search([('jdy_sync', '=', False)])
            action = self.env.ref('base_setup.action_general_configuration').read()[0]
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        for emp in emp_list:
            data = {
                'name': emp.name,
                'number': 'V14-' + str(emp.id),
                'gender': '1' if emp.gender == 'male' else '0',
                'mobile': emp.mobile_phone or '',
                'email': emp.work_email or '',
                'idnumber': emp.identification_id or ''
            }
            if emp.jdy_id:
                data['id'] = emp.jdy_id
            # 保存员工到精斗云
            raw = requests.post('http://api.kingdee.com/jdy/basedata/emp_save',
                                params=params, data=json.dumps(data), headers=headers, verify=False)
            if not raw.json().get('success'):
                raise UserError(u'员工写入精斗云失败，错误为：' + raw.json().get('description_cn', ' ') +
                                raw.json().get('message', ' '))
            # 取得jdy返回的员工id
            if not raw.json().get('data').get('success'):
                raise UserError(raw.json().get('data').get('errorInfo', ' ')[0].get('msg'))
            jdy_emp_id = raw.json().get('data').get('successPkIds')[0]
            # 将精斗云的员工id与编码记录在odoo的部门中
            emp.write({
                'jdy_id': jdy_emp_id,
                'jdy_number': 'V14-' + str(emp.id),
                'jdy_sync': True
            })
        return action
