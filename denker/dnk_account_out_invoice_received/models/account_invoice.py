# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.addons import decimal_precision as dp
from odoo import models, fields, api

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    dnk_customer_received = fields.Boolean(
        string="- Customer Received")
