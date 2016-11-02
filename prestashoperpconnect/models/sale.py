# -*- coding: utf-8 -*-
import openerp.addons.decimal_precision as dp

from openerp import api, fields, models


class SaleOrderState(models.Model):
    _name = 'sale.order.state'

    name = fields.Char('Name', size=128, translate=True)
    company_id = fields.Many2one('res.company', 'Company', required=True)
    prestashop_bind_ids = fields.One2many(
        'prestashop.sale.order.state',
        'openerp_id',
        string="Prestashop Bindings"
    )


class PrestashopSaleOrderState(models.Model):
    _name = 'prestashop.sale.order.state'
    _inherit = 'prestashop.binding'
    _inherits = {'sale.order.state': 'openerp_id'}

    openerp_state_ids = fields.One2many(
        'sale.order.state.list',
        'prestashop_state_id',
        'OpenERP States'
    )
    openerp_id = fields.Many2one(
        'sale.order.state',
        string='Sale Order State',
        required=True,
        ondelete='cascade'
    )


class SaleOrderStateList(models.Model):
    _name = 'sale.order.state.list'

    name = fields.Selection(
        [
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done')
        ],
        'OpenERP State',
        required=True
    )
    prestashop_state_id = fields.Many2one(
        'prestashop.sale.order.state',
        'Prestashop State'
    )
    prestashop_id = fields.Integer(
        related = 'prestashop_state_id.prestashop_id',
        string='Prestashop ID',
        readonly=True,
        store=True
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    prestashop_bind_ids = fields.One2many(
        'prestashop.sale.order',
        'openerp_id',
        string="Prestashop Bindings"
    )


class PrestashopSaleOrder(models.Model):
    _name = 'prestashop.sale.order'
    _inherit = 'prestashop.binding'
    _inherits = {'sale.order': 'openerp_id'}

    openerp_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade'
    )
    prestashop_order_line_ids = fields.One2many(
        'prestashop.sale.order.line',
        'prestashop_order_id',
        'Prestashop Order Lines'
    )
    prestashop_discount_line_ids = fields.One2many(
        'prestashop.sale.order.line.discount',
        'prestashop_order_id',
        'Prestashop Discount Lines'
    )
    prestashop_invoice_number = fields.Char(
        'PrestaShop Invoice Number', size=64
    )
    prestashop_delivery_number = fields.Char(
        'PrestaShop Delivery Number', size=64
    )
    total_amount = fields.Float(
        'Total amount in Prestashop',
        digits_compute=dp.get_precision('Account'),
        readonly=True
    )
    total_amount_tax = fields.Float(
        'Total tax in Prestashop',
        digits_compute=dp.get_precision('Account'),
        readonly=True
    )


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    prestashop_bind_ids = fields.One2many(
        'prestashop.sale.order.line',
        'openerp_id',
        string="PrestaShop Bindings"
    )
    prestashop_discount_bind_ids = fields.One2many(
        'prestashop.sale.order.line.discount',
        'openerp_id',
        string="PrestaShop Discount Bindings"
    )


class PrestashopSaleOrderLine(models.Model):
    _name = 'prestashop.sale.order.line'
    _inherit = 'prestashop.binding'
    _inherits = {'sale.order.line': 'openerp_id'}

    openerp_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order line',
        required=True,
        ondelete='cascade'
    )
    prestashop_order_id = fields.Many2one(
        'prestashop.sale.order',
        'Prestashop Sale Order',
        required=True,
        ondelete='cascade',
        select=True
    )

    @api.model
    def create(self, vals):
        prestashop_order_id = vals['prestashop_order_id']
        info = self.env['prestashop.sale.order'].browse(prestashop_order_id)
        vals['order_id'] = info.openerp_id.id
        return super(PrestashopSaleOrderLine, self).create(vals)


class PrestashopSaleOrderLineDiscount(models.Model):
    _name = 'prestashop.sale.order.line.discount'
    _inherit = 'prestashop.binding'
    _inherits = {'sale.order.line': 'openerp_id'}

    openerp_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order line',
        required=True,
        ondelete='cascade'
    )
    prestashop_order_id = fields.Many2one(
        'prestashop.sale.order',
        'Prestashop Sale Order',
        required=True,
        ondelete='cascade',
        select=True
    )
