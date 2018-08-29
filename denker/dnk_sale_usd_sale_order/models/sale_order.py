# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class AddAmountUSDtoSaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    @api.onchange('amount_untaxed')
    def _update_untaxed_amount_usd(self):
        res_currency_rate = self.env['res.currency.rate']
        date = self._context.get('date') or fields.Datetime.now()
        for rec in self:
            if rec.pricelist_id.currency_id.name  == 'USD':
                rec.amount_untaxed_usd = rec.amount_untaxed
            elif rec.pricelist_id.currency_id.name  == 'MXN':
                exchange_rate = res_currency_rate.search([('currency_id', '=', rec.pricelist_id.currency_id.id), ('name', '<=', date)], limit=1, order="name desc").rate
                rec.amount_untaxed_usd = amount_untaxed * exchange_rate
            else: rec.amount_untaxed_usd = 1.0


    amount_untaxed_usd = fields.Float('Untaxed Amount USD', compute='_update_untaxed_amount_usd', store=True)
