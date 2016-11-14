# -*- coding: utf-8 -*-
from decimal import Decimal

from openerp.tools.translate import _
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper,
    ExportMapper
)
from ..backend import prestashop
from ..connector import add_checkpoint
from backend_adapter import GenericAdapter
from backend_adapter import PrestaShopCRUDAdapter
from openerp.addons.connector_ecommerce.unit.sale_order_onchange import (
    SaleOrderOnChange)
from openerp.addons.connector.connector import Binder
from openerp.addons.connector.unit.mapper import only_create



class PrestashopImportMapper(ImportMapper):
    
    #get_openerp_id is deprecated use the binder intead
    #we should have only 1 way to map the field to avoid error
    def get_openerp_id(self, model, prestashop_id):
        '''
        Returns an openerp id from a model name and a prestashop_id.

        This permits to find the openerp id through the external application
        model in Erp.
        '''
        binder = self.binder_for(model)
        erp_ps_id = binder.to_openerp(prestashop_id)
        if erp_ps_id is None:
            return None

        return erp_ps_id.openerp_id.id

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def prestashop_id(self, record):
        return {'prestashop_id': record['id']}


@prestashop
class PartnerCategoryImportMapper(PrestashopImportMapper):
    _model_name = 'prestashop.res.partner.category'

    direct = [
        ('name', 'name'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
    ]


@prestashop
class PartnerImportMapper(PrestashopImportMapper):
    _model_name = 'prestashop.res.partner'

    direct = [
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('email', 'email'),
        ('newsletter', 'newsletter'),
        ('company', 'company'),
        ('active', 'active'),
        ('note', 'comment'),
        ('id_default_group', 'default_category_id'),
    ]

    @mapping
    def pricelist(self, record):
        binder = self.unit_for(Binder, 'prestashop.groups.pricelist')
        pricelist_id = binder.to_openerp(record['id_default_group'], unwrap=True)
        if not pricelist_id:
            return {}
        return {'property_product_pricelist': pricelist_id.id}

    @mapping
    def birthday(self, record):
        if record['birthday'] in ['0000-00-00', '']:
            return {}
        return {'birthday': record['birthday']}

    @mapping
    def name(self, record):
        name = ""
        if record['firstname']:
            name += record['firstname']
        if record['lastname']:
            if len(name) != 0:
                name += " "
            name += record['lastname']
        return {'name': name}

    @mapping
    def groups(self, record):
        groups = record.get('associations', {}).get('groups', {}).get('group', [])
        if not isinstance(groups, list):
            groups = [groups]
        partner_categories = []
        for group in groups:
            binder = self.binder_for(
                'prestashop.res.partner.category'
            )
            category_id = binder.to_openerp(group['id'])
            partner_categories.append(category_id)

        return {'group_ids': [(6, 0, [c.id for c in partner_categories])]}


    @mapping
    def lang(self, record):
        binder = self.binder_for('prestashop.res.lang')
        erp_lang_id = None
        if record.get('id_lang'):
            erp_lang = binder.to_openerp(record['id_lang'], unwrap=True)
        if erp_lang is None:
            data_obj = self.session.env.get('ir.model.data')
            erp_lang_id = data_obj.get_object_reference(
                'base',
                'lang_en')[1]
            model = self.session.env.get('res.lang')
            erp_lang = model.browse(erp_lang_id)
        return {'lang': erp_lang.code}

    @mapping
    def customer(self, record):
        return {'customer': True}

    @mapping
    def is_company(self, record):
        return {'is_company': False}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


@prestashop
class SupplierMapper(PrestashopImportMapper):
    _model_name = 'prestashop.supplier'

    direct = [
        ('name', 'name'),
        ('id', 'prestashop_id'),
        ('active', 'active'),
    ]

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def supplier(self, record):
        return {
            'supplier': True,
            'is_company': True,
            'customer': False,
        }

    @mapping
    def image(self, record):
        supplier_image_adapter = self.unit_for(
            PrestaShopCRUDAdapter, 'prestashop.supplier.image'
        )
        try:
            return {'image': supplier_image_adapter.read(record['id'])}
        except:
            return {}


@prestashop
class AddressImportMapper(PrestashopImportMapper):
    _model_name = 'prestashop.address'

    direct = [
        ('address1', 'street'),
        ('address2', 'street2'),
        ('city', 'city'),
        ('other', 'comment'),
        ('phone', 'phone'),
        ('phone_mobile', 'mobile'),
        ('postcode', 'zip'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('id_customer', 'prestashop_partner_id'),
    ]

    @mapping
    def parent_id(self, record):
        binder = self.binder_for('prestashop.res.partner')
        parent = binder.to_openerp(record['id_customer'], unwrap=True)
        if record['vat_number']:
            vat_number = record['vat_number'].replace('.', '').replace(' ', '')
            parent.write(
                {'vat': vat_number}
            )
        return {'parent_id': parent.id}

    def _check_vat(self, vat):
        vat_country, vat_number = vat[:2].lower(), vat[2:]
        return self.session.pool['res.partner'].simple_vat_check(
            self.session.cr,
            self.session.uid,
            vat_country,
            vat_number,
            context=self.session.context
        )

    @mapping
    def name(self, record):
        name = ""
        if record['firstname']:
            name += record['firstname']
        if record['lastname']:
            if name:
                name += " "
            name += record['lastname']
        if record['alias']:
            if name:
                name += " "
            name += '('+record['alias']+')'
        return {'name': name}

    @mapping
    def customer(self, record):
        return {'customer': True}
    
    @mapping
    def country(self, record):
        if record.get('id_country'):
            binder = self.binder_for('prestashop.res.country')
            erp_country_id = binder.to_openerp(record['id_country'], unwrap=True)
            return {'country_id': erp_country_id.id}
        return {}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

@prestashop
class SaleOrderStateMapper(PrestashopImportMapper):
    _model_name = 'prestashop.sale.order.state'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


@prestashop
class SaleOrderMapper(PrestashopImportMapper):
    _model_name = 'prestashop.sale.order'

    direct = [
        ('date_add', 'date_order'),
        ('invoice_number','prestashop_invoice_number'),
        ('delivery_number','prestashop_delivery_number'),
        ('total_paid', 'total_amount'),
    ]

    def _get_sale_order_lines(self, record):
        orders = record['associations'].get('order_rows', {}).get('order_row', [])
        if isinstance(orders, dict):
            return [orders]
        return orders

    children = [
        (
            _get_sale_order_lines,
            'prestashop_order_line_ids',
            'prestashop.sale.order.line'
        ),
    ]

    def _map_child(self, map_record, from_attr, to_attr, model_name):
        source = map_record.source
        # TODO patch ImportMapper in connector to support callable
        if callable(from_attr):
            child_records = from_attr(self, source)
        else:
            child_records = source[from_attr]

        children = []
        for child_record in child_records:
            adapter = self.unit_for(GenericAdapter,
                                                        model_name)
            detail_record = adapter.read(child_record['id'])

            mapper = self._get_map_child_unit(model_name)
            items = mapper.get_items(
                [detail_record], map_record, to_attr, options=self.options
            )
            children.extend(items)

        discount_lines = self._get_discounts_lines(source)
        children.extend(discount_lines)
        return children

    def _get_discounts_lines(self, record):
        if record['total_discounts'] == '0.00':
            return []
        adapter = self.unit_for(
            GenericAdapter, 'prestashop.sale.order.line.discount')
        discount_ids = adapter.search({'filter[id_order]': record['id']})
        discount_mappers = []
        for discount_id in discount_ids:
            discount = adapter.read(discount_id)
            mapper = self._init_child_mapper(
                'prestashop.sale.order.line.discount')
            mapper.convert_child(discount, parent_values=record)
            discount_mappers.append(mapper)
        return discount_mappers

    def _sale_order_exists(self, name):
        ids = self.session.env['sale.order'].search([
            ('name', '=', name),
            ('company_id', '=', self.backend_record.company_id.id),
        ])
        return len(ids) == 1

    @mapping
    def name(self, record):
        basename = record['reference']
        if not self._sale_order_exists(basename):
            return {"name": basename}
        i = 1
        name = basename + '_%d' % (i)
        while self._sale_order_exists(name):
            i += 1
            name = basename + '_%d' % (i)
        return {"name": name}

    @mapping
    def shipping(self, record):
        shipping_tax_incl = float(record['total_shipping_tax_incl'])
        shipping_tax_excl = float(record['total_shipping_tax_excl'])
        return {
            'shipping_amount_tax_included': shipping_tax_incl,
            'shipping_amount_tax_excluded': shipping_tax_excl,
        }

    # @mapping
    # def shop_id(self, record):
    #     if record['id_shop'] == '0':
    #         shop_ids = self.session.search('prestashop.shop', [
    #             ('backend_id', '=', self.backend_record.id)
    #         ])
    #         shop = self.session.read('prestashop.shop', shop_ids[0], ['openerp_id'])
    #         return {'shop_id': shop['openerp_id'][0]}
    #     return {'shop_id': self.get_openerp_id(
    #         'prestashop.shop',
    #         record['id_shop']
    #     )}

    @mapping
    def partner_id(self, record):
        return {'partner_id': self.get_openerp_id(
            'prestashop.res.partner',
            record['id_customer']
        )}

    @mapping
    def partner_invoice_id(self, record):
        return {'partner_invoice_id': self.get_openerp_id(
            'prestashop.address',
            record['id_address_invoice']
        )}

    @mapping
    def partner_shipping_id(self, record):
        return {'partner_shipping_id': self.get_openerp_id(
            'prestashop.address',
            record['id_address_delivery']
        )}

    @mapping
    def pricelist_id(self, record):
        return {'pricelist_id': 1}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def payment(self, record):
        method_ids = self.session.env['account.payment.method'].search(
            [
                ('name', '=', record['payment']),
                # ('company_id', '=', self.backend_record.company_id.id),
            ]
        )
        assert method_ids, ("Payment method '%s' has not been found ; "
                            "you should create it manually (in Sales->"
                            "Configuration->Sales->Payment Methods" %
                            record['payment'])
        method_id = method_ids[0]
        return {'payment_method_id': method_id}

    @mapping
    def carrier_id(self, record):
        if record['id_carrier'] == '0':
            return {}
        return {'carrier_id': self.get_openerp_id(
            'prestashop.delivery.carrier',
            record['id_carrier']
        )}

    @mapping
    def total_tax_amount(self, record):
        tax = float(record['total_paid_tax_incl'])\
                - float(record['total_paid_tax_excl'])
        return {'total_amount_tax': tax}

    def _after_mapping(self, result):
        sess = self.session
        backend = self.backend_record
        order_line_ids = []
        if 'prestashop_order_line_ids' in result:
            order_line_ids = result['prestashop_order_line_ids']
        taxes_included = backend.taxes_included
        with self.session.change_context({'is_tax_included': taxes_included}):
            result = sess.pool['sale.order']._convert_special_fields(
                sess.cr,
                sess.uid,
                result,
                order_line_ids,
                sess.context
            )
        onchange = self.unit_for(SaleOrderOnChange)
        order_line_ids = []
        if 'prestashop_order_line_ids' in result:
            order_line_ids = result['prestashop_order_line_ids']
        return onchange.play(result, order_line_ids)


@prestashop
class SaleOrderLineMapper(PrestashopImportMapper):
    _model_name = 'prestashop.sale.order.line'

    direct = [
        ('product_name', 'name'),
        ('id', 'sequence'),
        ('product_quantity', 'product_uom_qty'),
        ('reduction_percent', 'discount'),
    ]

    @mapping
    def prestashop_id(self, record):
        return {'prestashop_id': record['id']}

    @mapping
    def price_unit(self, record):
        if self.backend_record.taxes_included:
            key = 'unit_price_tax_incl'
        else:
            key = 'unit_price_tax_excl'
        if record['reduction_percent']:
            reduction = Decimal(record['reduction_percent'])
            price = Decimal(record[key])
            price_unit = price / ((100 - reduction) / 100) 
        else:
            price_unit = record[key]
        return {'price_unit': price_unit}

    @mapping
    def product_id(self, record):
        if ('product_attribute_id' in record and
                record['product_attribute_id'] != '0'):
            combination_binder = self.binder_for(
                'prestashop.product.combination')
            product_id = combination_binder.to_openerp(
                record['product_attribute_id'],
                unwrap=True
            )
        else:
            product_id = self.get_openerp_id(
                'prestashop.product.product',
                record['product_id']
            )
            if product_id is None:
                return self.tax_id(record)
        return {'product_id': product_id}

    def _find_tax(self, ps_tax_id):
        binder = self.binder_for('prestashop.account.tax')
        openerp_id = binder.to_openerp(ps_tax_id, unwrap=True)
        tax = self.session.read('account.tax', openerp_id, ['price_include', 'related_inc_tax_id'])
        if self.backend_record.taxes_included and not tax['price_include'] and tax['related_inc_tax_id']:
            return tax['related_inc_tax_id'][0]
        return openerp_id
        
    def tax_id(self, record):
        taxes = record.get('associations', {}).get('taxes', {}).get('tax', [])
        if not isinstance(taxes, list):
            taxes = [taxes]
        result = []
        for tax in taxes:
            openerp_id = self._find_tax(tax['id'])
            if openerp_id:
                result.append(openerp_id)
        if result:
            return {'tax_id': [(6, 0, result)]}
        return {}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class SaleOrderLineDiscount(PrestashopImportMapper):
    _model_name = 'prestashop.sale.order.line.discount'
    
    direct = []

    @mapping
    def discount(self, record):
        return {
            'name': _('Discount %s') % (record['name']),
            'product_uom_qty': 1,
        }

    @mapping
    def price_unit(self, record):
        if self.backend_record.taxes_included:
            price_unit = record['value']
        else:
            price_unit = record['value_tax_excl']
        if price_unit[0] != '-':
            price_unit = '-' + price_unit
        return {'price_unit': price_unit}

    @mapping
    def product_id(self, record):
        if self.backend_record.discount_product_id:
            return {'product_id': self.backend_record.discount_product_id.id}
        data_obj = self.session.pool.get('ir.model.data')
        model_name, product_id = data_obj.get_object_reference(
            self.session.cr,
            self.session.uid,
            'connector_ecommerce',
            'product_product_discount'
        )
        return {'product_id': product_id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class TaxGroupMapper(PrestashopImportMapper):
    _model_name = 'prestashop.account.tax.group'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


@prestashop
class SupplierInfoMapper(PrestashopImportMapper):
    _model_name = 'prestashop.product.supplierinfo'

    direct = [
        ('product_supplier_reference', 'product_code'),
    ]

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def name(self, record):
        binder = self.unit_for(Binder, 'prestashop.supplier')
        partner = binder.to_openerp(record['id_supplier'], unwrap=True)
        return {'name': partner.id}

    @mapping
    def product_id(self, record):
        if record['id_product_attribute'] != '0':
            binder = self.unit_for(Binder, 'prestashop.product.combination')
            product = binder.to_openerp(record['id_product_attribute'], unwrap=True)
        else:
            binder = self.unit_for(Binder, 'prestashop.product.product')    
            product = binder.to_openerp(record['id_product'], unwrap=True)
        
        return {'product_id': product.id}

    @mapping
    def required(self, record):
        return {'min_qty': 0.0, 'delay': 1}

class PrestashopExportMapper(ExportMapper):

    def _map_direct(self, record, from_attr, to_attr):
        res = super(PrestashopExportMapper, self)._map_direct(record,
                                                              from_attr,
                                                              to_attr)
        column = self.model._all_columns[from_attr].column
        if column._type == 'boolean':
            return res and 1 or 0
        return res


class TranslationPrestashopExportMapper(PrestashopExportMapper):

    def convert(self, records_by_language, fields=None):
        self.records_by_language = records_by_language
        first_key = records_by_language.keys()[0]
        self._convert(records_by_language[first_key], fields=fields)
        self._data.update(self.convert_languages(self.translatable_fields))

    def convert_languages(self, translatable_fields):
        res = {}
        for from_attr, to_attr in translatable_fields:
            value = {'language': []}
            for language_id, record in self.records_by_language.items():
                value['language'].append({
                    'attrs': {'id': str(language_id)},
                    'value': record[from_attr]
                })
            res[to_attr] = value
        return res


@prestashop
class MailMessageMapper(PrestashopImportMapper):
    _model_name = 'prestashop.mail.message'

    direct = [
        ('message', 'body'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def type(self, record):
        return {'type': 'comment'}

    @mapping
    def object_ref(self, record):
        binder = self.unit_for(
            Binder, 'prestashop.sale.order'
        )
        order_id = binder.to_openerp(record['id_order'], unwrap=True)
        return {
            'model': 'sale.order',
            'res_id': order_id,
        }

    @mapping
    def author_id(self, record):
        if record['id_customer'] != '0':
            binder = self.unit_for(Binder, 'prestashop.res.partner')
            partner_id = binder.to_openerp(record['id_customer'], unwrap=True)
            return {'author_id': partner_id}
        return {}


@prestashop
class MrpBomMapper(PrestashopImportMapper):
    _model_name = ['prestashop.mrp.bom', 'prestashop.combination.mrp.bom']

    direct = []

    @mapping
    def static(self, record):
        return {
            'type': 'phantom',
            'product_qty': 1,
        }

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def product_id(self, record):
        binder = self.unit_for(Binder, 'prestashop.product.product')
        product_id = binder.to_openerp(record['id'], unwrap=True)

        product = self.session.browse('product.product', product_id)
        return {
            'product_id': product_id,
            'product_uom': product.uom_id.id,
        }

    @mapping
    @only_create
    def bom_lines(self, record):
        lines = []
        bundle = record.get('associations', {}).get('product_bundle', {})
        if 'products' not in bundle:
            return {}
        binder = self.unit_for(
            Binder, 'prestashop.product.product',
        )
        products = bundle['products']
        if not isinstance(products, list):
            products = [products]
        for product in products:
            product_oerp_id = binder.to_openerp(product['id'], unwrap=True)
            product_oerp = self.session.browse('product.product', product_oerp_id)
            lines.append((0, 0, {
                'product_id': product_oerp_id,
                'product_qty': int(product['quantity']) or 1,
                'product_uom': product_oerp.uom_id.id,
            }))
        return {'bom_lines': lines}


@prestashop
class ProductPricelistMapper(PrestashopImportMapper):
    _model_name = 'prestashop.groups.pricelist'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def static(self, record):
        return {'active': True, 'type': 'sale'}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    @only_create
    def versions(self, record):
        item = {
            'min_quantity': 0,
            'sequence': 5,
            'base': 1,
            'price_discount': - float(record['reduction']) / 100.0,
        }
        version = {
            'name': 'Version',
            'active': True,
            'items_id': [(0, 0, item)],
        }
        return {'version_id': [(0, 0, version)]}
