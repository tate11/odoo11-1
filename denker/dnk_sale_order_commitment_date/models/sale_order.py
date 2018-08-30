# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models, _
from .functions import add_business_days, next_business_day
from openerp.exceptions import ValidationError


class SaleOrder(models.Model):
    """Add several date fields to Sales Orders, computed or user-entered"""
    _inherit = 'sale.order'

    commitment_date = fields.Datetime(string='- Recommitment Date', store=True,
                                      help="Date by which the products are sure to be delivered. This is "
                                           "a date that you can promise to the customer, based on the "
                                           "Product Lead Times.", track_visibility='onchange')
    dnk_original_commitment_date = fields.Datetime(string='- Commitment Date', store=True,
                                  help="Once the Sale Oder was confirmed this field can be modified but only if "
                                       "a notification is sent to the customer.", readonly=True)
    dnk_commitment_date_changed = fields.Boolean(string='Commitment Date Changed?', default=False, copy=False, store=True)

    # Sobreescribir la función _compute_commitment_date para que calcule la
    # Fecha Compromiso a partir de la  "Confirmación del Pedido" y no de
    # date_order que es la fecha de creación del pedido
    #@api.depends('date_order', 'order_line.customer_lead')
    @api.depends('dnk_commitment_date_changed', 'order_line.customer_lead')
    def _compute_commitment_date(self):
        # Compute the commitment date
        for order in self:
            if order.state == 'sale':
                dates_list = []
                confirmation_date = fields.Datetime.from_string(order.confirmation_date)
                for line in order.order_line.filtered(lambda x: x.state != 'cancel' and not x._is_delivery()):
                    dt = fields.Datetime.from_string(line.requested_date)
                    dates_list.append(dt)
                if dates_list:
                    commitment_date = max(dates_list) if order.picking_policy == 'direct' else max(dates_list)
                    order.commitment_date = fields.Datetime.to_string(commitment_date)
                if order.dnk_original_commitment_date != False:
                    order.dnk_commitment_date_changed = True
                    #self.send_warning_message()

    @api.onchange('commitment_date')
    @api.multi
    def send_warning_message(self):
        for order in self:
            if order.state == 'sale':
                warning = {}
                title = _('Commitment date has been changed!')
                message = _('The commintment date has been changed. The customer is going to be notified automatically at saving the Order.')
                warning = {
                        'title': title,
                        'message': message,
                }
                if warning:
                    return {'warning': warning}

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
            for line in order.order_line:
                # Si la Fecha Solicitada no está establecida, calcularla
                if line.requested_date == False:
                    line.requested_date = next_business_day(confirmation_date + timedelta(days=line.customer_lead or 0.0))
                    #line.requested_date = add_business_days(confirmation_date, line.customer_lead or 0.0)
                else:
                    # Si la Fecha Solicitada está establecida verificar si es mayor a la "Fecha Calculada" de Entrega
                    calculated_lead_time = next_business_day(confirmation_date + timedelta(days=line.customer_lead or 0.0))
                    # calculated_lead_time = add_business_days(confirmation_date, line.customer_lead or 0.0)
                    line_requested_date = fields.Datetime.from_string(line.requested_date)
                    # print("calculated_lead_time", type(calculated_lead_time), calculated_lead_time)
                    # print("line_requested_date", type(line_requested_date), line_requested_date)
                    if calculated_lead_time > line_requested_date:
                        # Enviar mensaje de Error
                        raise ValidationError(_('You cannot delivering before the Product Lead Time plus Transit Days of the Sales Channel.\n')
                                            + _("Please modify the Requested Date of \"" + line.product_id.name + "\" product."))
            order.dnk_commitment_date_changed = False

            if not order.dnk_original_commitment_date:
                order.dnk_original_commitment_date = order.commitment_date
        return res

    #        if self.env.context.get('send_email'):
    #            self.force_quotation_send()

    @api.multi
    def action_quotation_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('sale', 'email_template_edi_sale')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "sale.mail_template_data_notification_email_sale_order",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        commitment_date_changed = self.dnk_commitment_date_changed
        if commitment_date_changed:
            for order in self:
                if order.state == 'sale' and order.partner_id.dnk_recommitment_notification == True:
                    # Env iar correo al cliente informándole el cambio en la Fecha Compromiso
                    template_obj = self.env['mail.template'].search([('name','=','Dnk - Commitment Date - Send by Email')], limit=1)
                    body = self.env['mail.template'].render_template(template_obj.body_html, 'sale.order', self.id)
                    if template_obj:
                        mail_values = {
                            'subject': self.env['mail.template'].render_template(template_obj.subject, 'sale.order', self.id),
                            'body_html': body,
                            'email_to': order.partner_id.email,
                            'email_from': self.env['mail.template'].render_template(template_obj.email_from, 'sale.order', self.id),
                            'res_id': order.id,
                            'model': 'sale.order',
                            'body': body,
                        }
                        create_and_send_email = self.env['mail.mail'].create(mail_values).send()

        return res


    @api.multi
    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for order in self:
            order.dnk_commitment_date_changed = False
            order.commitment_date = False
            order.dnk_original_commitment_date = False
            for line in order.order_line:
                line.requested_date = False
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def _onchange_product_id_set_customer_lead(self):
        self.customer_lead = self.product_id.sale_delay + self.order_id.team_id.dnk_transit_days
