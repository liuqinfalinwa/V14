# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

from odoo import fields, models, api
import requests, json
from odoo.exceptions import UserError


class HrDepartment(models.Model):
    _inherit = "hr.department"

    jdy_id = fields.Char(u"精斗云id", copy=False)
    jdy_number = fields.Char(u'精斗云部门编码', copy=False)
    jdy_parent_id = fields.Char(u'精斗云上级部门id', copy=False)
    jdy_sync = fields.Boolean(u"是否与精斗云已同步", copy=False)

    @api.model
    def create(self, vals):
        res = super(HrDepartment, self).create(vals)
        if self._context.get('tracking_disable'):
            return res
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        # 取得精斗云顶层部门id
        raw_top_dept = requests.post('http://api.kingdee.com/jdy/basedata/dept_list',
                                     params=params, data=json.dumps({'search': '100000'}), headers=headers, verify=False)
        top_dept_id = raw_top_dept.json().get('data').get('rows')[0].get('id')
        parent_id = self.env['hr.department'].browse(vals.get('parent_id'))
        # parentorg_id需写入精斗云的上级部门ID
        data = {
            'name': vals.get('name'),
            'parentorg_id': str(parent_id.jdy_id or top_dept_id) if parent_id else str(top_dept_id)
        }
        # 保存部门到精斗云
        raw = requests.post('http://api.kingdee.com/jdy/basedata/dept_save',
                            params=params, data=json.dumps(data), headers=headers, verify=False)
        if not raw.json().get('success'):
            raise UserError(u'部门写入精斗云失败，错误为：' + raw.json().get('description_cn', ' ') +
                            raw.json().get('message', ' '))
        # 取得jdy返回的部门id，用起获取jdy自动编码的部门编号
        jdy_dept_id = raw.json().get('data').get('successPkIds')[0]
        raw_dept = requests.post('http://api.kingdee.com/jdy/basedata/dept_detail', params=params,
                                 data=json.dumps({'id': jdy_dept_id}), headers=headers, verify=False)
        # 将精斗云的部门id与编码记录在odoo的部门中
        res.write({
            'jdy_id': jdy_dept_id,
            'jdy_number': raw_dept.json().get('data').get('number'),
            'jdy_parent_id': raw_dept.json().get('data').get('parent_id'),
            'jdy_sync': True
        })
        return res

    def sync_dept_to_jdy(self):
        # 给出返回action
        action = self.env.ref('hr.hr_department_tree_action').read()[0]
        dept_list = self
        if len(self) == 0:
            dept_list = self.env['hr.department'].search([('jdy_sync', '=', False)])
            action = self.env.ref('base_setup.action_general_configuration').read()[0]
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        # 取得精斗云顶层部门id
        raw_top_dept = requests.post('http://api.kingdee.com/jdy/basedata/dept_list',
                                     params=params, data=json.dumps({'search': '100000'}), headers=headers,
                                     verify=False)
        top_dept_id = raw_top_dept.json().get('data').get('rows')[0].get('id')
        for dept in dept_list:
            # parentorg_id需写入精斗云的上级部门ID
            data = {
                'name': dept.name,
                'parentorg_id': str(dept.parent_id.jdy_id or top_dept_id)
            }
            if dept.jdy_id:
                data['id'] = dept.jdy_id
                data['number'] = dept.jdy_number
            # 保存部门到精斗云
            raw = requests.post('http://api.kingdee.com/jdy/basedata/dept_save',
                                params=params, data=json.dumps(data), headers=headers, verify=False)
            if not raw.json().get('success'):
                raise UserError(u'部门写入精斗云失败，错误为：' + raw.json().get('description_cn', ' ') + raw.json().get('message', ' '))
            # 取得jdy返回的部门id，用起获取jdy自动编码的部门编号
            if not raw.json().get('data').get('success'):
                raise UserError(raw.json().get('data').get('errorInfo', ' ')[0].get('msg'))
            jdy_dept_id = raw.json().get('data').get('successPkIds')[0]
            raw_dept = requests.post('http://api.kingdee.com/jdy/basedata/dept_detail', params=params,
                                     data=json.dumps({'id': jdy_dept_id}), headers=headers, verify=False)
            # 将精斗云的部门id与编码记录在odoo的部门中
            dept.write({
                'jdy_id': jdy_dept_id,
                'jdy_number': raw_dept.json().get('data').get('number'),
                'jdy_parent_id': raw_dept.json().get('data').get('parent_id'),
                'jdy_sync': True
            })
        return action
