# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

from odoo import fields, models, api
import requests, json
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    jdy_customer_id = fields.Char(u"精斗云客户id", copy=False)
    jdy_supplier_id = fields.Char(u"精斗云供应商id", copy=False)
    jdy_customer_number = fields.Char(u'精斗云客户编码', copy=False)
    jdy_supplier_number = fields.Char(u'精斗云供应商编码', copy=False)
    jdy_supplier_sync = fields.Boolean(u"供应商是否与精斗云已同步", copy=False)
    jdy_customer_sync = fields.Boolean(u"客户是否与精斗云已同步", copy=False)

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if self._context.get('tracking_disable'):
            return res
        supplier_data = customer_data = {}
        # 优先判断如果只是新增联系人，则不同步到jdy，可节省呼叫API次数
        if res.supplier_rank > 0 and res.company_type == 'company':
            supplier_data = res._prepare_data()
            del supplier_data['contractpersons']
        if res.customer_rank > 0 and res.company_type == 'company':
            customer_data = res._prepare_data()
            del customer_data['bomentity']
        if not supplier_data and not customer_data:
            return res
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        # 保存供应商到精斗云
        if supplier_data:
            raw = requests.post('http://api.kingdee.com/jdy/basedata/supplier_save',
                                params=params, data=json.dumps(supplier_data), headers=headers, verify=False)
        # 保存客户到精斗云
        if customer_data:
            raw = requests.post('http://api.kingdee.com/jdy/basedata/customer_save',
                                params=params, data=json.dumps(customer_data), headers=headers, verify=False)
        if not raw.json().get('success'):
            raise UserError(u'Partner写入精斗云失败，错误为：' + raw.json().get('description_cn', ' ') +
                            raw.json().get('message', ' '))
        # 取得jdy返回的id
        jdy_id = raw.json().get('data').get('successPkIds')[0]
        # 将精斗云的id与编码记录在odoo中
        afterrun = {}
        if supplier_data:
            afterrun['jdy_supplier_sync'] = True
            afterrun['jdy_supplier_id'] = jdy_id
            afterrun['jdy_supplier_number'] = 'V14-' + str(res.id)
        if customer_data:
            afterrun['jdy_customer_sync'] = True
            afterrun['jdy_customer_id'] = jdy_id
            afterrun['jdy_customer_number'] = 'V14-' + str(res.id)
        res.write(afterrun)
        return res

    def _prepare_data(self):
        self.ensure_one()
        data = {
            'name': self.name,
            'number': 'V14-' + str(self.id),
            'remark': self.comment or ''
        }
        if self.user_id.employee_id.jdy_id:
            data['salerid_id'] = self.user_id.employee_id.jdy_id
        children = []
        for child in self.child_ids:
            children.append({
                'contactperson': child.name,
                'phone': child.phone or '',
                'mobile': child.mobile or '',
                'email': child.email or '',
                'id': child.id
            })
        data['bomentity'] = children
        data['contractpersons'] = children
        return data

    def sync_partner_to_jdy(self):
        # 给出返回action
        action = {}
        if self.customer_rank > 0:
            customer_list = self
        if self.supplier_rank > 0:
            supplier_list = self
        if len(self) == 0:
            # 从系统设定的地方做批量上传
            customer_list = self.env['res.partner'].search([
                ('customer_rank', '>', 0), ('jdy_customer_sync', '=', False), ('company_type', '=', 'company')])
            supplier_list = self.env['res.partner'].search([
                ('supplier_rank', '>', 0), ('jdy_supplier_sync', '=', False), ('company_type', '=', 'company')])
            action = self.env.ref('base_setup.action_general_configuration').read()[0]
        info = self.env["jdy.connection"].sudo().get_connect_info()
        headers = info.get('headers')
        params = info.get('params')
        if self.customer_rank or len(self) == 0:
            for customer in customer_list:
                data = customer._prepare_data()
                del data['bomentity']
                if customer.jdy_customer_id:
                    data['id'] = customer.jdy_customer_id
                    data['number'] = customer.jdy_customer_number
                # 保存客户到精斗云
                raw = requests.post('http://api.kingdee.com/jdy/basedata/customer_save',
                                    params=params, data=json.dumps(data), headers=headers, verify=False)
                if not raw.json().get('success'):
                    raise UserError(u'客户写入精斗云失败，错误为：' + raw.json().get('description_cn', ' ') +
                                    raw.json().get('message', ' '))
                # 取得jdy返回的id
                if not raw.json().get('data').get('success'):
                    raise UserError(raw.json().get('data').get('errorInfo', ' ')[0].get('msg'))
                jdy_id = raw.json().get('data').get('successPkIds')[0]
                # 将精斗云的id与编码记录在odoo的中
                customer.write({
                    'jdy_customer_id': jdy_id,
                    'jdy_customer_number': 'V14-' + str(customer.id),
                    'jdy_customer_sync': True
                })
        if self.supplier_rank or len(self) == 0:
            for supplier in supplier_list:
                data = supplier._prepare_data()
                del data['contractpersons']
                if supplier.jdy_supplier_id:
                    data['id'] = supplier.jdy_supplier_id
                    data['number'] = supplier.jdy_supplier_number
                # 保存供应商到精斗云
                raw = requests.post('http://api.kingdee.com/jdy/basedata/supplier_save',
                                    params=params, data=json.dumps(data), headers=headers, verify=False)
                if not raw.json().get('success'):
                    raise UserError(u'供应商写入精斗云失败，错误为：' + raw.json().get('description_cn', ' ') +
                                    raw.json().get('message', ' '))
                # 取得jdy返回的id
                if not raw.json().get('data').get('success'):
                    raise UserError(raw.json().get('data').get('errorInfo', ' ')[0].get('msg'))
                jdy_id = raw.json().get('data').get('successPkIds')[0]
                # 将精斗云的id与编码记录在odoo的中
                supplier.write({
                    'jdy_supplier_id': jdy_id,
                    'jdy_supplier_number': 'V14-' + str(supplier.id),
                    'jdy_supplier_sync': True
                })
        return action
