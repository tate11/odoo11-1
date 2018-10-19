# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.addons import decimal_precision as dp
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    dnk_theoretical_cost = fields.Float(
        string="- Theoretical Cost",
        compute='_compute_theoretical_cost',
        inverse='_set_theoretical_cost',
        digits=dp.get_precision('Product Price'), groups="base.group_user")


    @api.one
    def _set_theoretical_cost(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.dnk_theoretical_cost = self.dnk_theoretical_cost


    @api.depends('product_variant_ids', 'product_variant_ids.standard_price')
    def _compute_theoretical_cost(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.dnk_theoretical_cost = template.product_variant_ids.dnk_theoretical_cost
        for template in (self - unique_variants):
            template.dnk_theoretical_cost = 0.0


class ProductProduct(models.Model):
    _inherit = "product.product"

    dnk_theoretical_cost = fields.Float(
        string="- Theoretical Cost",
        company_dependent=True,
        digits=dp.get_precision('Product Price'), groups="base.group_user")
