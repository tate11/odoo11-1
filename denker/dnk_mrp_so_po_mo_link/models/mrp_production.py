# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api
from odoo import models, fields


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    dnk_sale_order_line_ids = fields.Many2many(
                                comodel_name='sale.order.line', string="- Sale Order Line",
                                relation='dnk_production_order_sale_order_line_link',
                                column1='dnk_mrp_production_id', column2='sale_order_line_id',
                                compute='_compute_sale_order_by_origin',
                                readonly=True, store=True)

    @api.multi
    @api.depends('origin')
    def _compute_sale_order_by_origin(self):
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']
        for mrp_production in self:
            # Extraer los números de pedidos en la forma SO001, SO002, SO003
            if not mrp_production.origin:
                break
            origin_list = mrp_production.origin.replace(' ','').split(',')
            sale_orders_line_list = []
            for sale_order in origin_list:
                # Buscar el pedido de origin en el catálogo de pedidos
                sale_order = SaleOrder.search([('name', '=', sale_order)])
                if sale_order:
                    # Buscar la Línea de Pedido Correcta
                    for sale_order_line in sale_order.order_line:
                        if sale_order_line.product_id.id == mrp_production.product_id.id: # and \
                            # not sale_order_line.dnk_mrp_production_id:
                            # sale_order_line.product_uom_qty == mrp_production.product_qty and \
                            sale_orders_line_list.append(sale_order_line.id)
                            #mrp_production.sale_order_line_id = sale_order_line.id
                            sale_order_line.write({'dnk_mrp_production_id': mrp_production.id})
                            #sale_order_line.dnk_mrp_production_id = production.id
                            break

            mrp_production.dnk_sale_order_line_ids = sale_orders_line_list


    @api.multi
    @api.depends('procurement_group_id')
    def _compute_sale_order(self):
        for production in self:
            if production.procurement_group_id:
                sale_order = self.env['sale.order']
                sale = sale_order.search([('procurement_group_id', '=', production.procurement_group_id.id)])
                if sale:
                    # production.sale_order_id = sale.id
                    # Buscar la Línea de Pedido relacionada al pedido
                    for sale_order_line in sale.order_line:
                        if sale_order_line.product_id.id == production.product_id.id and \
                           sale_order_line.product_uom_qty == production.product_qty and \
                           not sale_order_line.dnk_mrp_production_id:
                            production.dnk_sale_order_line_ids = [sale_order_line.id]
                            sale_order_line.write({'dnk_mrp_production_id': production.id})
                            break
