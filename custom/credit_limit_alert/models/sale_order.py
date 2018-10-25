from odoo import models, fields, api, exceptions,_

class CreditLimitAlertSaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    permitted_credit_limit = fields.Boolean('Limite de credito excedido permitido', default=False)

    @api.one
    @api.multi
    def action_confirm(self):

        cr = self.env.cr
        cr.execute("select COALESCE(SUM(1),0) FROM account_invoice WHERE type='out_invoice' AND state='open' AND date_due<DATE(NOW()) AND partner_id='"+str(self.partner_id.id)+"'")
        facturas_vencidas = cr.fetchone()
        fac = max(facturas_vencidas)
        if fac >= 1 and self.payment_term_id.name != 'Immediate Payment' and self.permitted_credit_limit is not True:
            raise exceptions.ValidationError('Este cliente cuenta con facturas vencidas.')
        else:

            if self.partner_id.credit_limit != 0:
                if self.partner_id.credit + self.amount_total > self.partner_id.credit_limit:
                    if self.payment_term_id.name != 'Immediate Payment':
                        if self.permitted_credit_limit is not True:
                            self.avisado = True
                            raise exceptions.ValidationError('Este cliente ha exedido el limite de credito. Su limite actual es: '
                                                             + str(self.partner_id.credit_limit) +', actualmente tiene una deuda de: '
                                                             + str(self.partner_id.credit) + ' y disponible tiene '
                                                             + str(self.partner_id.credit_available)
                                                             + ', debe de autorizar el limite de credito excedido' )

            res = super(CreditLimitAlertSaleOrder, self).action_confirm()

            return res

class CreditLimitAlertStockPicking(models.Model):
    _name = "stock.picking"
    _inherit = 'stock.picking'

    
    allow_delivery = fields.Boolean('Permitir entrega con facturas vencidas', default=False)

    @api.multi
    def button_validate(self):
        self.ensure_one()
        cr = self.env.cr
        cr.execute("select COALESCE(SUM(1),0) FROM account_invoice WHERE type='out_invoice' AND state='open' AND date_due<DATE(NOW()) AND partner_id='"+str(self.partner_id.id)+"'")
        facturas_vencidas = cr.fetchone()
        fac = max(facturas_vencidas)
        if fac >= 1 and self.allow_delivery is not True:
            raise exceptions.ValidationError('Este cliente cuenta con facturas vencidas.')
        else:

            res = super(CreditLimitAlertStockPicking, self).button_validate()

            return res