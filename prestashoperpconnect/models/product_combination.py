'''
A product combination is a product with different attributes in prestashop.
In prestashop, we can sell a product or a combination of a product with some
attributes.

For example, for the iPod product we can found in demo data, it has some
combinations with different colors and different storage size.

We map that in OpenERP to a product.product with an attribute.set defined for
the main product.
'''

from openerp import api, fields, models

from openerp.addons.connector.session import ConnectorSession

from ..unit.import_synchronizer import import_record


class ProductProduct(models.Model):
    _inherit = 'product.product'

    prestashop_combinations_bind_ids = fields.One2many(
        'prestashop.product.combination',
        'openerp_id',
        string='PrestaShop Bindings (combinations)'
    )


class PrestashopProductCombination(models.Model):
    _name = 'prestashop.product.combination'
    _inherit = 'prestashop.binding'
    _inherits = {'product.product': 'openerp_id'}

    openerp_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        ondelete='cascade'
    )
    main_product_id = fields.Many2one(
        'prestashop.product.product',
        string='Main product',
        required=True,
        ondelete='cascade'
    )
    quantity = fields.Float(
        'Computed Quantity',
        help="Last computed quantity to send on Prestashop."
    )
    reference = fields.Char('Original reference')

    @api.model
    def recompute_prestashop_qty(self):
        for product in self:
            new_qty = self._prestashop_qty(product)
            product.write({quantity: new_qty})
        return True

    @api.model
    def _prestashop_qty(self, product):
        return product.qty_available
