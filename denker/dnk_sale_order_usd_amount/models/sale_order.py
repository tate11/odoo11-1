# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class AddAmountUSDtoSaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    @api.depends('amount_untaxed','pricelist_id')
    def _update_untaxed_amount_usd(self):
        res_currency_rate = self.env['res.currency.rate']
        date = self._context.get('date') or fields.Datetime.now()
        res_currency_usd_id = 3

        for rec in self:
            if rec.pricelist_id.currency_id.name  == 'USD':
                rec.dnk_amount_untaxed_usd = rec.amount_untaxed
                #for line in rec.order_line:
                #    line.dnk_price_subtotal_usd = line.price_subtotal
            elif rec.pricelist_id.currency_id.name  == 'MXN':
                exchange_rate = res_currency_rate.search([('currency_id', '=', res_currency_usd_id), ('name', '<=', date)], limit=1, order="name desc").rate
                rec.dnk_amount_untaxed_usd = rec.amount_untaxed * exchange_rate
                #for line in rec.order_line:
                #    line.dnk_price_subtotal_usd = line.price_subtotal * exchange_rate


    dnk_amount_untaxed_usd = fields.Float('- Untaxed Amount USD', compute="_update_untaxed_amount_usd", store=True)
