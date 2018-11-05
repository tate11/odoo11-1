# -*- coding: utf-8 -*-
{
    'name' : 'Product Development',
    'version' : '1',
    'author': 'Humanytek',
    'description': """

    """,
    'category' : 'MRP',
    'depends' : ['sale_crm', 'account', 'dnk_crm_opportunities', 'dnk_groups_categories'],
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/ir_attachment_view.xml',
        'views/product_development_view.xml',
        'views/crm_view.xml',
        'views/product_category_view.xml',
    ],
    'demo': [

    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
