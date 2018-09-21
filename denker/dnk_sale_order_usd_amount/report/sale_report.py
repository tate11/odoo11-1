# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    dnk_price_subtotal_usd = fields.Float('- Untaxed Total USD')
    
    def _select(self):
        return super(SaleReport, self)._select() + ",sum(l.dnk_price_subtotal_usd / COALESCE(cr.rate, 1.0)) as dnk_price_subtotal_usd "
