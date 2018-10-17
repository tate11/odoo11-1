# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class PurchaseOrderFile(models.Model):
    _inherit = ['sale.order']

    @api.model
    def action_confirm(self):
        res =super(PurchaseOrderFile, self).action_confirm()
        if self.partner_id.dnk_purchase_order_required and not self.dnk_purchase_order_file:
            raise ValidationError("The settings for this client requires a purchase order file.")
        return res


    dnk_purchase_order_name = fields.Char('- Purchase Order Name')
    dnk_purchase_order_file = fields.Binary('- Purchase Order File', attachment=True, store=True)
