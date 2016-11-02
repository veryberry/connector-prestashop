# -*- coding: utf-8 -*-
#############################################################################
#
#    Prestashoperpconnect : OpenERP-PrestaShop connector
#    Copyright (C) 2013 Akretion (http://www.akretion.com/)
#    Copyright (C) 2013 Camptocamp SA
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Sébastien BEAU <sebastien.beau@akretion.com>
#    @author: Guewen Baconnier
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import logging
import pytz
from datetime import datetime

from openerp import api, fields, models


from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.addons.connector.session import ConnectorSession
from ..unit.import_synchronizer import (
    import_batch,
    import_customers_since,
    import_orders_since,
    import_products,
    import_refunds,
    import_carriers,
    import_suppliers,
    import_record,
    export_product_quantities,
)
from ..unit.direct_binder import DirectBinder
from ..connector import get_environment

from openerp.addons.prestashoperpconnect.product import import_inventory

_logger = logging.getLogger(__name__)


class PrestashopBackend(models.Model):
    _name = 'prestashop.backend'
    _doc = 'Prestashop Backend'
    _inherit = 'connector.backend'

    _backend_type = 'prestashop'

    @api.model
    def _select_versions(self):
        """ Available versions

        Can be inherited to add custom versions.
        """
        return [('1.6', '1.6')]

    version = fields.Selection(
        _select_versions,
        string='Version',
        required=True)
    location = fields.Char('Location')
    webservice_key = fields.Char(
        'Webservice key',
        help="You have to put it in 'username' of the PrestaShop "
             "Webservice api path invite"
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        'Warehouse',
        required=True,
        help='Warehouse used to compute the stock quantities.'
    )
    taxes_included = fields.Boolean("Use tax included prices")
    import_partners_since = fields.Datetime('Import partners since')
    import_orders_since = fields.Datetime('Import Orders since')
    import_products_since = fields.Datetime('Import Products since')
    import_refunds_since = fields.Datetime('Import Refunds since')
    import_suppliers_since = fields.Datetime('Import Suppliers since')
    language_ids = fields.One2many(
        'prestashop.res.lang',
        'backend_id',
        'Languages'
    )
    company_id = fields.Many2one('res.company', 'Company', select=1, required=True)
    discount_product_id = fields.Many2one('product.product', 'Dicount Product', select=1, required=False)
    shipping_product_id = fields.Many2one('product.product', 'Shipping Product', select=1, required=False)

    _defaults = {
        company_id: lambda s: s.env.get('res.company')._company_default_get('prestashop.backend')
    }

    @api.multi
    def synchronize_metadata(self):
        # session = ConnectorSession(cr, uid, context=context)
        # for backend in self:
        #     for model in ('prestashop.shop.group',
        #                   'prestashop.shop'):
        #         # import directly, do not delay because this
        #         # is a fast operation, a direct return is fine
        #         # and it is simpler to import them sequentially
        #         import_batch(session, model, backend.id)
        return True

    @api.multi
    def synchronize_basedata(self):
        session = ConnectorSession.from_env(self.env)
        for backend in self:
            for model_name in [
                'prestashop.res.lang',
                'prestashop.res.country',
                'prestashop.res.currency',
                'prestashop.account.tax',
            ]:
                env = get_environment(session, model_name, backend.id)
                directBinder = env.get_connector_unit(DirectBinder)
                directBinder.run()

            import_batch(session, 'prestashop.account.tax.group', backend.id)
            import_batch(session, 'prestashop.sale.order.state', backend.id)
        return True

    @api.model
    def _date_as_user_tz(self, dtstr):
        if not dtstr:
            return None
        user = self.env.user
        timezone = pytz.timezone(user.partner_id.tz or 'utc')
        dt = datetime.strptime(dtstr, DEFAULT_SERVER_DATETIME_FORMAT)
        dt = pytz.utc.localize(dt)
        dt = dt.astimezone(timezone)
        return dt

    @api.multi
    def import_customers_since(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            since_date = self._date_as_user_tz(backend_record.import_partners_since)
            import_customers_since.delay(
                session,
                backend_record.id,
                since_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                priority=10,
            )

        return True

    @api.multi
    def import_products(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            since_date = self._date_as_user_tz(backend_record.import_products_since)
            import_products.delay(session, backend_record.id, since_date, priority=10)
        return True

    @api.multi
    def import_carriers(self):
        session = ConnectorSession.from_env(self.env)
        for backend in self:
            import_carriers.delay(session, backend.id, priority=10)
        return True

    @api.multi
    def update_product_stock_qty(self):
        session = ConnectorSession.from_env(self.env)
        export_product_quantities.delay(session, [b.id for b in self])
        return True

    @api.multi
    def import_stock_qty(self):
        session = ConnectorSession.from_env(self.env)
        for backend in self:
            import_inventory.delay(session, backend.id)

    @api.multi
    def import_sale_orders(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            since_date = self._date_as_user_tz(backend_record.import_orders_since)
            import_orders_since.delay(
                session,
                backend_record.id,
                since_date,
                priority=5,
            )
        return True

    @api.multi
    def import_payment_methods(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            import_batch.delay(session, 'payment.method', backend_record.id)
        return True

    @api.multi
    def import_refunds(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            since_date = self._date_as_user_tz(backend_record.import_refunds_since)
            import_refunds.delay(session, backend_record.id, since_date)
        return True

    @api.multi
    def import_suppliers(self):
        session = ConnectorSession.from_env(self.env)
        for backend_record in self:
            since_date = self._date_as_user_tz(backend_record.import_suppliers_since)
            import_suppliers.delay(session, backend_record.id, since_date)
        return True

    @api.model
    def _scheduler_update_product_stock_qty(self, domain=None):
        self.search(domain).update_product_stock_qty()

    @api.model
    def _scheduler_import_sale_orders(self, domain=None):
        self.search(domain).import_sale_orders()

    @api.model
    def _scheduler_import_customers(self, domain=None):
        self.search(domain).import_customers_since()

    @api.model
    def _scheduler_import_products(self, domain=None):
        self.search(domain).import_products()

    @api.model
    def _scheduler_import_carriers(self, domain=None):
        self.search(domain).import_carriers()

    @api.model
    def _scheduler_import_payment_methods(self, domain=None):
        self.search(domain).import_payment_methods()

    @api.model
    def _scheduler_import_refunds(self, domain=None):
        self.search(domain).import_refunds()

    @api.model
    def _scheduler_import_suppliers(self, domain=None):
        self.search(domain).import_suppliers()

    @api.model
    def import_record(self, backend_id, model_name, ext_id):
        session = ConnectorSession.from_env(self.env)
        import_record(session, model_name, backend_id, ext_id)
        return True


class PrestashopBinding(models.AbstractModel):
    _name = 'prestashop.binding'
    _inherit = 'external.binding'
    _description = 'PrestaShop Binding (abstract)'

    # openerp_id = openerp-side id must be declared in concrete model
    backend_id = fields.Many2one(
        'prestashop.backend',
        'PrestaShop Backend',
        required=True,
        ondelete='restrict')
    # TODO : do I keep the char like in Magento, or do I put a PrestaShop ?
    prestashop_id = fields.Integer('ID on PrestaShop')

    # the _sql_contraints cannot be there due to this bug:
    # https://bugs.launchpad.net/openobject-server/+bug/1151703

    @api.multi
    def resync(self):
        session = ConnectorSession.from_env(self.env)
        func = import_record
        if self.env.context.get('connector_delay'):
            func = import_record.delay
        for product in self:
            func(
                session,
                self._name,
                product.backend_id.id,
                product.prestashop_id
            )
        return True


class PrestashopResLang(models.Model):
    _name = 'prestashop.res.lang'
    _inherit = 'prestashop.binding'
    _inherits = {'res.lang': 'openerp_id'}

    openerp_id = fields.Many2one(
        'res.lang',
        string='Lang',
        required=True,
        ondelete='cascade'
    )
    active = fields.Boolean('Active in prestashop', default=False)

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A Lang with the same ID on Prestashop already exists.')
    ]


class ResLang(models.Model):
    _inherit = 'res.lang'

    prestashop_bind_ids = fields.One2many(
        'prestashop.res.lang',
        'openerp_id',
        string='prestashop Bindings',
        readonly=True)


class PrestashopResCountry(models.Model):
    _name = 'prestashop.res.country'
    _inherit = 'prestashop.binding'
    _inherits = {'res.country': 'openerp_id'}

    openerp_id = fields.Many2one(
        'res.country',
        string='Country',
        required=True,
        ondelete='cascade'
    )

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A Country with the same ID on prestashop already exists.')
    ]


class ResCountry(models.Model):
    _inherit = 'res.country'

    prestashop_bind_ids = fields.One2many(
        'prestashop.res.country',
        'openerp_id',
        string='prestashop Bindings',
        readonly=True
    )


class PrestashopResCurrency(models.Model):
    _name = 'prestashop.res.currency'
    _inherit = 'prestashop.binding'
    _inherits = {'res.currency': 'openerp_id'}

    openerp_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        ondelete='cascade'
    )

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A Currency with the same ID on prestashop already exists.')
    ]


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    prestashop_bind_ids = fields.One2many(
        'prestashop.res.currency',
        'openerp_id',
        string='prestashop Bindings',
        readonly=True
    )


class PrestashopAccountTax(models.Model):
    _name = 'prestashop.account.tax'
    _inherit = 'prestashop.binding'
    _inherits = {'account.tax': 'openerp_id'}

    openerp_id = fields.Many2one(
        'account.tax',
        string='Tax',
        required=True,
        ondelete='cascade'
    )

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A Tax with the same ID on prestashop already exists.')
    ]


class AccountTax(models.Model):
    _inherit = 'account.tax'

    prestashop_bind_ids = fields.One2many(
        'prestashop.account.tax',
        'openerp_id',
        string='prestashop Bindings',
        readonly=True
    )


class PrestashopAccountTaxGroup(models.Model):
    _name = 'prestashop.account.tax.group'
    _inherit = 'prestashop.binding'
    _inherits = {'account.tax.group': 'openerp_id'}

    openerp_id = fields.Many2one(
        'account.tax.group',
        string='Tax Group',
        required=True,
        ondelete='cascade'
    )

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A Tax Group with the same ID on prestashop already exists.')
    ]


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    prestashop_bind_ids = fields.One2many(
        'prestashop.account.tax.group',
        'openerp_id',
        string='Prestashop Bindings',
        readonly=True
    )
    company_id = fields.Many2one('res.company', 'Company', select=1, required=True)
