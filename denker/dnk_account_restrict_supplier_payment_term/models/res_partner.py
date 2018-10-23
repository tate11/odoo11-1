# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DnkRestrictSupplierPaymentTerm(models.Model):
    _inherit = "res.partner"

    @api.multi
    def _check_account_group(self):
        for rec in self:
            if self.env.user.has_group('dnk_accounting_groups.dnk_account_supplier_payment_term_admin') :
                rec.dnk_mod_payment_term = True
            else :
                rec.dnk_mod_payment_term = False

    dnk_mod_payment_term = fields.Boolean(String='- Edit Supplier Payment Term', compute='_check_account_group', store=False)
