# -*- coding: utf-8 -*-
{
    'name': "Denker - Sale Custom Views",

    'summary': """
        Este módulo hace cambios de Vistas de Contabilidad requeridos por Grupo Denker""",

    'description': """
        Mostrar el campo Concepto (communication) en la vista de lista de Pagos (account_payment).
    """,

    'author': "José Candelas",
    'website': "http://www.grupodenker.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '11.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['sale'],

    # always loaded
    'data': [
        #'security/sale_order_security.xml',
        'views/account_payment_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
