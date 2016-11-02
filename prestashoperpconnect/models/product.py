# -*- coding: utf-8 -*-
from openerp import api, fields, models

from openerp.addons.connector.session import ConnectorSession

from ..unit.import_synchronizer import import_record


class ProductCategory(models.Model):
    _inherit = 'product.category'

    prestashop_bind_ids = fields.One2many(
        'prestashop.product.category',
        'openerp_id',
        string="PrestaShop Bindings"
    )


class PrestashopProductCategory(models.Model):
    _name = 'prestashop.product.category'
    _inherit = 'prestashop.binding'
    _inherits = {'product.category': 'openerp_id'}

    openerp_id = fields.Many2one(
        'product.category',
        string='Product Category',
        required=True,
        ondelete='cascade'
    )
    date_add = fields.Datetime(
        'Created At (on PrestaShop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        'Updated At (on PrestaShop)',
        readonly=True
    )
    description = fields.Char('Description', translate=True)
    link_rewrite = fields.Char('Friendly URL', translate=True)
    meta_description = fields.Char('Meta description', translate=True)
    meta_keywords = fields.Char('Meta keywords', translate=True)
    meta_title = fields.Char('Meta title', translate=True)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    prestashop_bind_ids = fields.One2many(
        'prestashop.product.product',
        'openerp_id',
        string='PrestaShop Bindings'
    )

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default['prestashop_bind_ids'] = []
        return super(ProductProduct, self).copy(default=default)

    @api.multi
    def update_prestashop_quantities(self):
        for product in self:
            for prestashop_product in product.prestashop_bind_ids:
                prestashop_product.recompute_prestashop_qty()
            prestashop_combinations = product.prestashop_combinations_bind_ids
            for prestashop_combination in prestashop_combinations:
                prestashop_combination.recompute_prestashop_qty()
        return True


class PrestashopProductProduct(models.Model):
    _name = 'prestashop.product.product'
    _inherit = 'prestashop.binding'
    _inherits = {'product.product': 'openerp_id'}

    openerp_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        ondelete='cascade'
    )
    # TODO FIXME what name give to field present in
    # prestashop_product_product and product_product
    always_available = fields.Boolean(
        'Active',
        help='if check, this object is always available')
    quantity = fields.Float(
        'Computed Quantity',
        help="Last computed quantity to send on Prestashop."
    )
    description_html = fields.Html(
        'Description',
        translate=True,
        help="Description html from prestashop",
    )
    description_short_html = fields.Html(
        'Short Description',
        translate=True,
    )
    date_add = fields.Datetime(
        'Created At (on Presta)',
        readonly=True
    )
    date_upd = fields.Datetime(
        'Updated At (on Presta)',
        readonly=True
    )
    link_rewrite = fields.Char(
        'Friendly URL',
        translate=True,
        required=False,
    )
    combinations_ids = fields.One2many(
        'prestashop.product.combination',
        'main_product_id',
        string='Combinations'
    )
    reference = fields.Char('Original reference')

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         "A product with the same ID on Prestashop already exists")
    ]

    @api.multi
    def recompute_prestashop_qty(self):
        for product in self:
            backend = product.backend_id
            stock = backend.warehouse_id.lot_stock_id
            product.write({
                'quantity': product.with_context({
                    'location': stock.id
                }).read(['qty_available'])[0]['qty_available']
            })
        return True


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    prestashop_groups_bind_ids = fields.One2many(
        'prestashop.groups.pricelist',
        'openerp_id',
        string='Prestashop user groups'
    )


class PrestashopGroupsPricelist(models.Model):
    _name = 'prestashop.groups.pricelist'
    _inherit = 'prestashop.binding'
    _inherits = {'product.pricelist': 'openerp_id'}

    openerp_id = fields.Many2one(
        'product.pricelist',
        string='Openerp Pricelist',
        required=True,
        ondelete='cascade'
    )
