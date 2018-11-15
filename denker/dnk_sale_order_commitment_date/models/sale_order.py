# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models, _
from .functions import add_business_days, next_business_day
from openerp.exceptions import ValidationError


# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    """Add several date fields to Sales Orders, computed or user-entered"""
    _inherit = 'sale.order'

    # Eliminar del siguiente campo el parámetro: compute='_compute_commitment_date',
    dnk_commitment_date = fields.Datetime(string='- Commitment Date', store=True,
                                    help="Once the Sale Oder was confirmed this field can be modified but only if "
                                        "a notification is sent to the customer.", readonly=True)
    #dnk_reconfirmation_date = fields.Datetime(string='- Reconfirmation Date', store=True,
    #                                help="Date by which the products are sure to be delivered. This is "
    #                                     "a date that you can promise to the customer, based on the "
    #                                     "Product Lead Times.", track_visibility='onchange')
    #dnk_reconfirmation_date_changed = fields.Boolean(string='- Commitment Date Changed?',
    #                                default=False, copy=False, store=True)
    dnk_requested_date = fields.Datetime('- Requested Date', readonly=True, states={'draft': [('readonly', False)],
                                    'sent': [('readonly', False)]}, copy=False,
                                    help="Date by which the customer has requested the items to be "
                                         "delivered.\n"
                                         "When this Order gets confirmed, the Delivery Order's "
                                         "expected date will be computed based on this date and the "
                                         "Company's Security Delay.\n"
                                         "Leave this field empty if you want the Delivery Order to be "
                                         "processed as soon as possible. In that case the expected "
                                         "date will be computed using the default method: based on "
                                         "the Product Lead Times and the Company's Security Delay.")
    dnk_effective_date = fields.Date(compute='_compute_picking_ids', string='- Effective Date', store=True,
                                    help="Date on which the first Delivery Order was created.")


    # Recalcular el campo "customer_lead" al cambiar de Equipo de Ventas
    @api.multi
    @api.onchange('team_id')
    def _onchange_team_id_set_customer_lead(self):
        for order in self:
            for line in order.order_line:
                line.customer_lead = line.product_id.sale_delay + order.team_id.dnk_transit_days

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            confirmation_date = fields.Datetime.from_string(order.confirmation_date)
            # Colocar la bandera de Cambio de Fecho Compromiso en Falso, ya que
            # sólo me interesan los cambios a partir de que el pedido fue confirmado
            max_requested_date = False
            for line in order.order_line:
                # Si la Fecha Solicitada no está establecida, calcularla
                if line.dnk_requested_date == False:
                    line.dnk_requested_date = next_business_day(confirmation_date + timedelta(days=line.customer_lead or 0.0))
                    line.dnk_reconfirmation_date = line.dnk_requested_date
                    #line.dnk_requested_date = add_business_days(confirmation_date, line.customer_lead or 0.0)
                else:
                    # Si la Fecha Solicitada está establecida verificar si es mayor a la "Fecha Calculada" de Entrega
                    calculated_lead_time = next_business_day(confirmation_date + timedelta(days=line.customer_lead or 0.0))
                    # calculated_lead_time = add_business_days(confirmation_date, line.customer_lead or 0.0)
                    line_requested_date = fields.Datetime.from_string(line.dnk_requested_date)
                    # print("calculated_lead_time", type(calculated_lead_time), calculated_lead_time)
                    # print("line_requested_date", type(line_requested_date), line_requested_date)
                    if calculated_lead_time > line_requested_date:
                        # Enviar mensaje de Error
                        raise ValidationError(_('You cannot delivering before the Product Lead Time plus Transit Days of the Sales Channel.\n')
                                            + _("Please modify the Requested Date of \"[" + line.product_id.default_code + "] " + line.product_id.name + "\" product."))

                if max_requested_date == False:
                    max_requested_date = line.dnk_requested_date
                elif max_requested_date<line.dnk_requested_date:
                    max_requested_date = line.dnk_requested_date

            if not order.dnk_commitment_date:
                order.dnk_commitment_date = max_requested_date
        return res


    # Si se cancela el pedido, hacer todas las fechas nulas
    @api.multi
    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for order in self:
            order.dnk_commitment_date = False
            for line in order.order_line:
                line.dnk_requested_date = False
                line.dnk_reconfirmation_date_changed = False
                line.dnk_reconfirmation_date = False
        return res


    # Calcula la fecha de la primer entrega, campo "dnk_effective_date"
    def _compute_picking_ids(self):
        super(SaleOrder, self)._compute_picking_ids()
        for order in self:
            dates_list = []
            for pick in order.picking_ids:
                dates_list.append(fields.Datetime.from_string(pick.date))
            if dates_list:
                order.dnk_effective_date = fields.Datetime.to_string(min(dates_list))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    dnk_requested_date = fields.Datetime(string="- Requested Date")
    dnk_reconfirmation_date = fields.Datetime(string='- Reconfirmation Date', store=True,
                                    help="Date by which the products are sure to be delivered. This is "
                                         "a date that you can promise to the customer, based on the "
                                         "Product Lead Times.")
    dnk_reconfirmation_date_changed = fields.Boolean(string='- Commitment Date Changed?',
                                    default=False, copy=False, store=True)


    # Sumar los días de tránsito a los días de entrega de la línea del pedido
    @api.onchange('product_id')
    def _onchange_product_id_set_customer_lead(self):
        self.customer_lead = self.product_id.sale_delay + self.order_id.team_id.dnk_transit_days


    # Si el usuario cambia el campo "Fecha Reconfirmación", avisar al usuario que el cliente será notificado con un correo
    @api.multi
    @api.onchange('dnk_reconfirmation_date')
    def send_warning_message(self):
        for line in self:
            if line.order_id.state in ('sale', 'done') and line.dnk_reconfirmation_date != line.dnk_requested_date:
                # TO DO: Reprogramar entregas
                # Cuando sea posible, reprogramar las entregas y la órden de producción
                # for move in line.move_ids:
                #    pass move.date

                # Levantar la bandera para saber que el campo dnk_reconfirmation_date ha cambiado
                line.dnk_reconfirmation_date_changed = True
                warning = {}
                title = _('Commitment date has been changed!')
                message = _('The commintment date has been changed. The customer is going to be notified automatically at saving the Order.')
                warning = {
                        'title': title,
                        'message': message,
                }
                if warning:
                    return {'warning': warning}


    # Al crear el registro, escribir el nuevo campo 'dnk_requested_date'
    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        if res.order_id.dnk_requested_date and not res.dnk_requested_date:
            res.write({
                'dnk_requested_date': res.dnk_requested_date,
                'dnk_reconfirmation_date': res.dnk_reconfirmation_date,
                'dnk_reconfirmation_date_changed': res.dnk_reconfirmation_date_changed,
            })
        return res


    # Escribir el nuevo campo 'dnk_requested_date'
    @api.multi
    def write(self, vals):
        for line in self:
            if not line.dnk_requested_date and line.order_id.dnk_requested_date and\
                    'dnk_requested_date' not in vals:
                vals.update({
                    'dnk_requested_date': line.order_id.dnk_requested_date
                })

            if not line.dnk_requested_date and line.order_id.dnk_requested_date and\
                    'dnk_reconfirmation_date' not in vals:
                vals.update({
                    'dnk_reconfirmation_date': line.order_id.dnk_requested_date
                })

            if not line.dnk_requested_date and line.order_id.dnk_requested_date and\
                    'dnk_reconfirmation_date_changed' not in vals:
                vals.update({
                    'dnk_reconfirmation_date_changed': line.order_id.dnk_requested_date
                })
        res = super(SaleOrderLine, self).write(vals)

        commitment_date_changed = self.dnk_reconfirmation_date_changed
        if commitment_date_changed:
            for line in self:
                line.dnk_reconfirmation_date_changed = False
                if line.order_id.state in ('sale', 'done') and line.order_id.partner_id.dnk_reconfirmation_notification:
                    # Env iar correo al cliente informándole el cambio en la Fecha Compromiso
                    template_obj = self.env['mail.template'].search([('name','=','Dnk - Commitment Date - Send by Email')], limit=1)
                    body = self.env['mail.template'].render_template(template_obj.body_html, 'sale.order.line', line.id)
                    if template_obj:
                        mail_values = {
                            'subject': self.env['mail.template'].render_template(template_obj.subject, 'sale.order.line', line.id),
                            'body_html': body,
                            'email_to': line.order_id.partner_id.email,
                            'email_from': self.env['mail.template'].render_template(template_obj.email_from, 'sale.order.line', line.id),
                            'res_id': line.order_id.id,
                            'model': 'sale.order.line',
                            'body': body,
                        }
                        create_and_send_email = self.env['mail.mail'].create(mail_values).send()

        return res


    # Configurar la Fecha Planeada de las entregas del pedido
    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        vals = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        for line in self.filtered("order_id.dnk_requested_date"):
            date_planned = fields.Datetime.from_string(line.dnk_requested_date) - timedelta(days=line.order_id.company_id.security_lead)
            vals.update({
                'date_planned': fields.Datetime.to_string(date_planned),
            })
        return vals


    # Si el usuario cambia el campo "Fecha Reconfirmación", avisar al usuario que
    # la fecha de Reconfimación no debe ser menor a la Fecha de Confirmación
    @api.onchange('dnk_requested_date')
    def onchange_requested_date(self):
        """Warn if the requested dates is sooner than the commitment date"""
        # Si el pedido no está confirmado tomar la fecha actual, si no, la Fecha de Confirmación
        date = (fields.Datetime.from_string(self.order_id.confirmation_date) if self.order_id.confirmation_date else fields.Datetime.from_string(fields.Datetime.now())) + timedelta(days=self.product_id.sale_delay + self.order_id.team_id.dnk_transit_days)
        if (self.dnk_requested_date and fields.Datetime.from_string(self.dnk_requested_date) < date):
            return {'warning': {
                'title': _('Requested date is too soon!'),
                'message': _("The date requested by the customer is "
                             "sooner than the confirmation date or today plus dalay days and transit days. You may be "
                             "unable to honor the customer's request.")
                }
            }
