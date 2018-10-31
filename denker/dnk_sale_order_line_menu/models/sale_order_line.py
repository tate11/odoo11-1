# © 2016 OdooMRP team
# © 2016 AvanzOSC
# © 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Eficent Business and IT Consulting Services, S.L.
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    team_id = fields.Many2one('crm.team', 'Sales Channel', related='order_id.team_id', compute='_get_crm_team', store=True)


    @api.multi
    @api.depends('order_id.team_id')
    def _get_crm_team(self):
        for rec in self:
            if rec.order_id.team_id:
                rec.team_id = rec.order_id.team_id.id
        return
