# -*- encoding: utf-8 -*-

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    prestashop_bind_ids = fields.One2many(
        'prestashop.refund',
        'openerp_id',
        string="Prestashop Bindings"
    )

    @api.multi
    def action_move_create(self):
        so_obj = self.env.get('prestashop.sale.order')
        line_replacement = {}
        for invoice in self:
            sale_orders = so_obj.search([('name', '=', invoice.origin)])
            if not sale_orders:
                continue
            discount_product_id = sale_orders[0].backend_id.discount_product_id.id

            for invoice_line in invoice.invoice_line:
                if invoice_line.product_id.id != discount_product_id:
                    continue
                amount = invoice_line.price_subtotal
                if invoice.partner_id.parent_id:
                    partner_id = invoice.partner_id.parent_id.id
                else:
                    invoice.partner_id.id
                refund = self._find_refund(-1 * amount, partner_id)
                if refund:
                    self.env.get('account.invoice.line').unlink(invoice_line.id)
                    line_replacement[invoice.id] = refund.id
                    invoice.button_reset_taxes()

        result = super(AccountInvoice, self).action_move_create()
        # reconcile invoice with refund
        for invoice_id, refund_id in line_replacement.items():
            self._reconcile_invoice_refund(invoice_id, refund_id)
        return result

    @api.model
    def _reconcile_invoice_refund(self, invoice_id, refund_id):
        move_line_obj = self.env.get('account.move.line')
        invoice_obj = self.env.get('account.invoice')

        invoice = invoice_obj.browse(invoice_id)
        refund = invoice_obj.browse(refund_id)

        move_line_ids = move_line_obj.search([
            ('move_id', '=', invoice.move_id.id),
            ('debit', '!=', 0.0),
        ])
        move_line_ids += move_line_obj.search([
            ('move_id', '=', refund.move_id.id),
            ('credit', '!=', 0.0),
        ])
        move_line_ids.reconcile_partial()

    @api.model
    def _find_refund(self, amount, partner_id):
        refunds = self.search([
            ('amount_untaxed', '=', amount),
            ('type', '=', 'out_refund'),
            ('state', '=', 'open'),
            ('partner_id', '=', partner_id),
        ])
        if not refunds:
            return None
        return refunds[0]


class PrestashopRefund(models.Model):
    _name = 'prestashop.refund'
    _inherit = 'prestashop.binding'
    _inherits = {'account.invoice': 'openerp_id'}

    openerp_id = fields.Many2one(
        'account.invoice',
        string='Invoice',
        required=True,
        ondelete='cascade',
    )
