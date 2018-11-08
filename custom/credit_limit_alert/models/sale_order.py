from odoo import models, fields, api, exceptions,_
from datetime import datetime, date, time, timedelta
import calendar

class CreditLimitAlertSaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    permitted_credit_limit = fields.Boolean('Limite de credito excedido permitido', default=False)
    paid_sale_order = fields.Boolean('Pedido Pagado', default=False)

    @api.one
    @api.multi
    def action_confirm(self):
        current_date = date.today() - timedelta(days=15)
        cr = self.env.cr
        cr.execute("select COALESCE(SUM(1),0) FROM account_invoice WHERE type='out_invoice' AND state='open' AND date_due<='"+str(current_date)+"' AND partner_id='"+str(self.partner_id.id)+"'")
        facturas_vencidas = cr.fetchone()
        fac = max(facturas_vencidas)


        if self.partner_id.block_sales==True:
            raise exceptions.ValidationError('El cliente tiene bloqueadas las ventas')

        if not self.payment_term_id:
            raise exceptions.ValidationError('Necesita seleccionar un plazo de pago.')

        if (self.payment_term_id.id==1 and self.paid_sale_order!=True):
            raise exceptions.ValidationError('Si el pago es inmediato necesita validar que esta orden esté pagada')

        if (fac >= 1 and self.payment_term_id.id != 1 and self.permitted_credit_limit is not True):
            raise exceptions.ValidationError('Este cliente cuenta con facturas vencidas.')
        else:

            if self.partner_id.credit_limit != 0:
                credit = self.env['res.currency']._compute(self.partner_id.currency_id,self.currency_id,self.partner_id.credit)
                credit_limit = self.env['res.currency']._compute(self.partner_id.currency_id,self.currency_id,self.partner_id.credit_limit)
                if credit + self.amount_total > credit_limit:
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
        current_date = date.today() - timedelta(days=15)
        cr = self.env.cr
        cr.execute("select COALESCE(SUM(1),0) FROM account_invoice WHERE type='out_invoice' AND state='open' AND date_due<='"+str(current_date)+"' AND partner_id='"+str(self.partner_id.id)+"'")
        facturas_vencidas = cr.fetchone()
        fac = max(facturas_vencidas)
        if fac >= 1 and self.allow_delivery is not True:
            raise exceptions.ValidationError('Este cliente cuenta con facturas vencidas.')
        else:

            res = super(CreditLimitAlertStockPicking, self).button_validate()

            return res
