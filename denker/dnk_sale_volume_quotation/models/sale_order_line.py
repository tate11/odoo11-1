# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from openerp.exceptions import UserError, RedirectWarning, ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    dnk_minimum_quantity = fields.Text('- Minimun Qty.', store=True)
    dnk_volume_prices = fields.Text('- Volume Prices', store=True)


    @api.model
    def write(self, vals):
        dnk_minimum_quantity, dnk_volume_prices = self._get_volume_prices_per_sale_line(self.order_id, self.product_id, self.product_uom, self.product_uom_qty, self.price_unit)
        vals_append = {
            'dnk_minimum_quantity': dnk_minimum_quantity,
            'dnk_volume_prices': dnk_volume_prices,
        }
        vals.update(vals_append)
        return super(SaleOrderLine, self).write(vals)


    @api.model
    def create(self, vals):
        sale_order = self.env['sale.order'].browse(vals.get('order_id'))
        product = self.env['product.product'].browse(vals.get('product_id'))
        product_uom = self.env['product.uom'].browse(vals.get('product_uom'))
        product_uom_qty = vals.get('product_uom_qty')
        price_unit = vals.get('price_unit')

        dnk_minimum_quantity, dnk_volume_prices = self._get_volume_prices_per_sale_line(sale_order, product, product_uom, product_uom_qty, price_unit)

        vals_append = {
            'dnk_minimum_quantity': dnk_minimum_quantity,
            'dnk_volume_prices': dnk_volume_prices,
        }
        vals.update(vals_append)

        return super(SaleOrderLine, self).create(vals)


    def _formatLang(self, value, show_currency=True):
            lang = self.order_id.partner_id.lang
            lang_objs = self.env['res.lang'].search([('code', '=', lang)])
            if not lang_objs:
                lang_objs = self.env['res.lang'].search([], limit=1)
            lang_obj = lang_objs[0]

            decimals_quantity = self.env['decimal.precision'].search([('name', '=', 'Product Price')])
            if decimals_quantity:
                decimals_quantity = decimals_quantity[0].digits
            else:
                decimals_quantity = 2

            res = lang_obj.format('%.' + str(decimals_quantity) + 'f', value, grouping=True, monetary=True)
            currency_obj = self.order_id.currency_id

            if show_currency and currency_obj and currency_obj.symbol:
                if currency_obj.position == 'after':
                    res = '%s%s' % (res, currency_obj.symbol)
                elif currency_obj and currency_obj.position == 'before':
                    res = '%s%s' % (currency_obj.symbol, res)
            return res


    def _get_volume_prices_per_sale_line(self, order_id, product_id, product_uom, product_uom_qty, price_unit):
        if not (product_id and order_id.partner_id
           and order_id.pricelist_id):
            return('', '')

        # Si la lista de precios tiene un sólo "Item" entonces para extraer
        # las cantidades ir a la lista de precios base del "Item"
        if len(order_id.pricelist_id.item_ids) == 1:
            if order_id.pricelist_id.item_ids[0].base == 'list_price':
                search_pricelist_id = order_id.pricelist_id.item_ids[0].base_pricelist_id
            else:
                search_pricelist_id = order_id.pricelist_id.id
        else:
            search_pricelist_id = order_id.pricelist_id.id

        # Falta buscar por Variante
        ProductPriceListItem = self.env['product.pricelist.item']
        price_list = ProductPriceListItem.search(
            [('pricelist_id', '=', search_pricelist_id),
             ('product_tmpl_id', '=', product_id.product_tmpl_id.id)], order="min_quantity DESC")

        context_partner = dict(self.env.context, partner_id=order_id.partner_id.id, date=order_id.date_order)
        pricelist_context = dict(context_partner, uom=product_uom.id)

        str_prices = ''
        str_mininimum_quantity = ''
        unit_price = ""
        for price in price_list:
            if price.id and price.min_quantity:
                # Marco: Usa esta función para extraer la precio de la tarifa pública de la siguiente manera:
                # Comando para debuggear:
                # sudo su - odoo9dev -c "/opt/odoo9dev/odoo/openerp-server --config /etc/odoo9dev/odoo.conf --dev"
                # tarifa_publica = self.env['res.lang'].search([('name', '=', 'Nombre de la tarifa publica')])
                # context_partner = dict(self.env.context, partner_id=order_id.partner_id.id, date=order_id.date_order)
                # pricelist_context = dict(context_partner, uom=product_uom.id)
                # tarifa_publica..with_context(pricelist_context).get_product_price_rule(product_id, price.min_quantity, order_id.partner_id)
                unit_price, rule_id = order_id.pricelist_id.with_context(pricelist_context).get_product_price_rule(product_id, price.min_quantity, order_id.partner_id)
                str_prices += self._formatLang(unit_price, show_currency=False) + "\n"
                str_mininimum_quantity += '{:0,.0f}'.format(price.min_quantity) + "\n"

        # En caso de que el producto no se encuentre en la lista de precio, calcular el precio
        if unit_price == "":
            product = product_id.with_context(
                lang=order_id.partner_id.lang,
                partner=order_id.partner_id.id,
                quantity=product_uom_qty,
                date=order_id.date_order,
                pricelist=order_id.pricelist_id.id,
                uom=product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            unit_price, rule_id = order_id.pricelist_id.with_context(pricelist_context).get_product_price_rule(product_id, product_uom_qty, order_id.partner_id)
            price_unit = unit_price

        if str_prices == "" or str_mininimum_quantity == "":
            str_prices = self._formatLang(price_unit, show_currency=False)
            str_mininimum_quantity = '{:0,.0f}'.format(product_uom_qty)

        return(str_mininimum_quantity, str_prices)


    @api.onchange('product_id')
    def _get_volume_prices(self):
        for sale_order_line in self:
            dnk_minimum_quantity, dnk_volume_prices = self._get_volume_prices_per_sale_line(sale_order_line.order_id, sale_order_line.product_id, self.product_uom, self.product_uom_qty, self.price_unit)

            sale_order_line.dnk_minimum_quantity = dnk_minimum_quantity
            sale_order_line.dnk_volume_prices = dnk_volume_prices


    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
