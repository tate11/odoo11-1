# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class InvoicePurchaseOrderFile(models.Model):
    _inherit = ['account.invoice']



    dnk_purchase_order_name = fields.Char('- Purchase Order Name', related='dnk_sale_order.dnk_purchase_order_name')
    dnk_purchase_order_file = fields.Binary( '- Purchase Order File',
        related='dnk_sale_order.dnk_purchase_order_file',
        readonly=True, store=False)

    @api.multi
    @api.onchange('dnk_purchase_order_name')
    def update_name_ref(self):
        for account in self:
            if account.dnk_purchase_order_name:
                account.name = account.dnk_purchase_order_name.lower().replace('.pdf','').upper()

class AttacchPurchaseOrderFile(models.Model):
    _inherit =['ir.actions.report']

    @api.model
    def postprocess_pdf_report(self, record, buffer):
        res = super(AttacchPurchaseOrderFile,self).postprocess_pdf_report(record, buffer)
        if record.partner_id.dnk_attach_purchase_order and record.dnk_purchase_order_file and record.dnk_purchase_order_name:
            order_attachment_vals= {
                'res_name': record.name,
                'res_id' : record.id,
                'name': str(record.dnk_purchase_order_name),
                'datas': record.dnk_purchase_order_file,
                'res_model': 'account.invoice',
                'datas_fname': record.dnk_purchase_order_name,
                'type': 'binary'
            }
            order_attachment = None
            try:
                    order_attachment = self.env['ir.attachment'].create(order_attachment_vals)
            except AccessError:
                _logger.info("Cannot save Purchase Order %r as attachment", order_attachment_vals['name'])
            else:
                _logger.info('The Purchase Order %s is now saved in the database', order_attachment_vals['name'])
            return res

class MailComposerToAttachPurchaseOrder(models.TransientModel):
    _inherit =['mail.compose.message']

    @api.model
    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        res = super(MailComposerToAttachPurchaseOrder,self).onchange_template_id(template_id, composition_mode, model, res_id)
        Attachments = self.env['ir.attachment']
        Accounts= self.env['account.invoice']
        account = Accounts.search([('id','=',res_id)]) #Me traigo la factura para acceder al nombre del archivo
        if account:
            #Busco el adjunto que guardé en la función postprocess_pdf_report
            order_attach = Attachments.search([('res_id','=',res_id),('name','=',account.dnk_purchase_order_name)], limit=1, order="id desc")
            if order_attach and account.partner_id.dnk_attach_purchase_order:
                res['value']['attachment_ids'][0][2].append(order_attach.id)
        return res
