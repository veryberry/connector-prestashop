from openerp import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    prestashop_supplier_bind_ids = fields.One2many(
        'prestashop.supplier',
        'openerp_id',
        string="Prestashop supplier bindings",
    )


class PrestashopSupplier(models.Model):
    _name = 'prestashop.supplier'
    _inherit = 'prestashop.binding'
    _inherits = {'res.partner': 'openerp_id'}

    openerp_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade'
    )


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    prestashop_bind_ids = fields.One2many(
        'prestashop.product.supplierinfo',
        'openerp_id',
        string="Prestashop bindings",
    )


class PrestashopProductSupplierinfo(models.Model):
    _name = 'prestashop.product.supplierinfo'
    _inherit = 'prestashop.binding'
    _inherits = {'product.supplierinfo': 'openerp_id'}

    openerp_id = fields.Many2one(
        'product.supplierinfo',
        string='Supplier info',
        required=True,
        ondelete='cascade'
    )
