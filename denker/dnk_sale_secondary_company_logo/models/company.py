# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import os

from odoo import api, fields, models, _

class Company(models.Model):
    _inherit = "res.company"

    def _get_logo(self):
        return base64.b64encode(open(os.path.join(tools.config['root_path'], 'addons', 'base', 'res', 'res_company_logo.png'), 'rb') .read())

    logo2 = fields.Binary(string="Secondary Logo", attachment=True, default=_get_logo,
        help="This field holds the image used as avatar for this contact, limited to 1024x1024px",)
