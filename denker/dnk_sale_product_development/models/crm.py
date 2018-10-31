# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class CRMLead(models.Model):
    _inherit = "crm.lead"
    
    dp_number = fields.Integer(compute='_compute_dp', string="Number of DPs")
    dp_ids = fields.One2many('product.development', 'opp_id', string='Orders')
    piezas_por_producto = fields.Integer("Piezas por Producto")
    precio_por_pieza = fields.Float("Precio por Pieza")
    planned_revenue = fields.Float(compute="_get_revenue", string='Expected Revenue', track_visibility='always', store=True)

    @api.depends('dp_ids')
    def _compute_dp(self):
        for lead in self:
            lead.dp_number = len(lead.dp_ids)
   
    @api.multi     
    @api.depends('piezas_por_producto','precio_por_pieza')
    def _get_revenue(self):
        for lead in self:
            lead.planned_revenue = lead.piezas_por_producto * lead.precio_por_pieza
    
    
    
    
