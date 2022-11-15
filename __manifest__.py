{
    'name': "Rayn OPD",

    'summary': """
        This module is for FTEs & Contractual Employees for OPD treatment""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Numdesk",
    'website': "http://www.numdesk.com",
    'category': 'Health',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr_expense', 'account'],

    # always loaded
    'data': [
        'security/rayn_opd_security.xml',
        'security/ir.model.access.csv',
        'wizard/opd_payment_register.xml',
        'views/views.xml',
        'views/config.xml',
        'views/product.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
# -*- coding: utf-8 -*-
