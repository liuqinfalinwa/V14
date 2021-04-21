# -*- coding: utf-8 -*-

#  Copyright (c) 2021 PaulLu LGPL-3

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    jdy_username = fields.Char(u'精斗云用户名(必须为手机号)')
    jdy_password = fields.Char(u'精斗云密码')
    jdy_client_id = fields.Char(u'精斗云应用ID')
    jdy_client_secret = fields.Char(u'应用Secret')
    jdy_account_id = fields.Char(u'精斗云Account ID')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            jdy_username=self.env['ir.config_parameter'].sudo().get_param(
                'account_integration_jdy.username') or '',
            jdy_password=self.env['ir.config_parameter'].sudo().get_param(
                'account_integration_jdy.password') or '',
            jdy_client_id=self.env['ir.config_parameter'].sudo().get_param(
                'account_integration_jdy.client_id') or '',
            jdy_client_secret=self.env['ir.config_parameter'].sudo().get_param(
                'account_integration_jdy.client_secret') or '',
            jdy_account_id=self.env['ir.config_parameter'].sudo().get_param(
                'account_integration_jdy.account_id') or ''
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('account_integration_jdy.username', self.jdy_username)
        self.env['ir.config_parameter'].sudo().set_param('account_integration_jdy.password', self.jdy_password)
        self.env['ir.config_parameter'].sudo().set_param('account_integration_jdy.client_id', self.jdy_client_id)
        self.env['ir.config_parameter'].sudo().set_param('account_integration_jdy.client_secret', self.jdy_client_secret)
        self.env['ir.config_parameter'].sudo().set_param('account_integration_jdy.account_id', self.jdy_account_id)

    def action_sync_dept(self):
        self.env['hr.department'].sync_dept_to_jdy()

    def action_sync_emp(self):
        self.ensure_one()
        self.env['hr.employee'].sync_emp_to_jdy()

    def action_sync_partner(self):
        self.ensure_one()
        self.env['res.partner'].sync_partner_to_jdy()

    def action_sync_account(self):
        self.ensure_one()
        self.env['account.account'].get_account_from_jdy()

    def action_sync_analytic_account(self):
        self.ensure_one()
        self.env['jdy.analytic.account'].sudo().sync_jdy_analytic_account()

    def action_sync_journal(self):
        self.ensure_one()
        self.env['account.journal'].sudo().sync_jdy_account()

    def action_sync_voucher_type(self):
        self.ensure_one()
        self.env['jdy.voucher.type'].sudo().sync_jdy_voucher_type()

    def action_sync_entries(self):
        self.ensure_one()
        self.env['account.move'].sudo().sync_account_move_to_jdy()

    def action_sync_invoice(self):
        self.ensure_one()
        self.env['account.move'].sudo().sync_invoice_to_jdy()

    def action_sync_bill(self):
        self.ensure_one()
        self.env['account.move'].sudo().sync_bill_to_jdy()

    def action_sync_settlement(self):
        self.ensure_one()
        self.env['jdy.settlement.type'].sudo().sync_jdy_settlement_type()
        self.env['jdy.settlement.account'].sudo().sync_jdy_settlement_account()
