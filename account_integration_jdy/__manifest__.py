# -*- coding: utf-8 -*-
#  Copyright (c) 2021 PaulLu LGPL-3
{
    'name': '对接金蝶云星辰同步财务模块',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 35,
    'summary': 'Accounting Integration JDY: Sync with JDY ERP',
    'website': "https://www.odoo-service.com",
    'category': 'Extra Tools',
    'version': '1.0',
    'description': """金蝶云星辰同步模块
""",
    'author': "Paul Lu",
    'depends': ['account', 'mail', 'hr'],
    'data': [
        'security/jdy_integration_security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/account_account.xml',
        'views/hr_department.xml',
        'views/hr_employee.xml',
        'views/res_partner.xml',
        'views/jdy_analytic_account.xml',
        'views/account_journal.xml',
        'views/jdy_voucher_type.xml',
        'views/account_move.xml',
        'views/jdy_settlement_account.xml',
        'views/jdy_settlement_type.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
    'support': 'luss613@gmail.com',
    'images': ['static/description/jdy_setting.png']
}
