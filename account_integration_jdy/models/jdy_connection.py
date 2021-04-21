# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

from odoo import fields, models, api
import requests, json
from odoo.exceptions import UserError
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class JdyConnection(models.Model):
    _name = "jdy.connection"
    _description = "Jdy Connection"

    # 取得jdy API相关数据
    def get_connect_info(self):
        params = self.env['ir.config_parameter'].sudo()
        username = params.get_param('account_integration_jdy.username', default='')
        password = params.get_param('account_integration_jdy.password', default='')
        client_id = params.get_param('account_integration_jdy.client_id', default='')
        client_secret = params.get_param('account_integration_jdy.client_secret', default='')
        account_id = params.get_param('account_integration_jdy.account_id', default='')
        if username == '' or password == '' or client_id == '' or client_secret == '':
            raise UserError(u'请检查精斗云配置，参数不可为空')
        raw = requests.get(
            url="https://api.kingdee.com/auth/user/access_token?client_id=%s&client_secret=%s&username=%s&password=%s"
                % (client_id, client_secret, username, password), verify=False)
        access_token = raw.json().get('data').get('access_token', '123')
        raw_group = requests.post(
            url="https://api.kingdee.com/jdy/sys/accountGroup?access_token=%s" % access_token, verify=False)
        if not raw_group.json().get('success'):
            raise UserError(u'获取精斗云账套信息失败，请联系管理员检查账号及系统权限设定')
        groups = [acc for acc in raw_group.json().get('data')[0].get('accountGroups') if acc.get('accountId') == account_id]
        if not groups:
            raise UserError(u'账套ID设定错误，请联系管理员检查账套ID设定')
        service_id = raw_group.json().get('data')[0].get('serviceId')
        group_id = groups[0].get('groupId')
        group_name = groups[0].get('groupName')
        headers = {
            'content-type': 'application/json',
            'charset': 'utf-8',
            'groupName': group_name,
            'accountId': account_id,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15"
        }
        params = {
            'access_token': access_token
        }
        return {
            'username': username,
            'password': password,
            'client_id': client_id,
            'client_secret': client_secret,
            'service_id': service_id,
            'account_id': account_id,
            'group_id': group_id,
            'group_name': group_name,
            'access_token': access_token,
            'params': params,
            'headers': headers
        }

