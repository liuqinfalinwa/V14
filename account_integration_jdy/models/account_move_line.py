# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

from odoo import fields, models, api
import requests, json
from odoo.exceptions import UserError
from datetime import datetime


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    jdy_analytic_dept = fields.Many2one('hr.department', string=u"部门分析项")
    jdy_analytic_emp = fields.Many2one('hr.employee', string=u"员工分析项")
    jdy_analytic_other = fields.Many2one('jdy.analytic.account', string='自定义分析项', domain=[('enable', '=', '1')])


