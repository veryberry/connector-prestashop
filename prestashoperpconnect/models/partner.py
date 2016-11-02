# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2012 Akretion                                               #
#   Author :                                                                  #
#           Sébastien BEAU <sebastien.beau@akretion.com>                      #
#           Benoît GUILLOT <benoit.guillot@akretion.com>                      #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

from openerp import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    prestashop_bind_ids = fields.One2many(
        'prestashop.res.partner', 'openerp_id',
        string="PrestaShop Bindings"
    )
    prestashop_address_bind_ids =  fields.One2many(
        'prestashop.address', 'openerp_id',
        string="PrestaShop Address Bindings"
    )


class PrestashopResPartner(models.Model):
    _name = 'prestashop.res.partner'
    _inherit = 'prestashop.binding'
    _inherits = {'res.partner': 'openerp_id'}

    # _rec_name = 'shop_group_id'

    openerp_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade'
    )
    backend_id = fields.Many2one(
        'prestashop.backend',
        # related='shop_group_id.backend_id',
        string='Prestashop Backend',
        readonly=True
    )
    group_ids = fields.Many2many(
        'prestashop.res.partner.category',
        'prestashop_category_partner',
        'partner_id',
        'category_id',
        string='PrestaShop Groups'
    )
    date_add = fields.Datetime(
        'Created At (on PrestaShop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        'Updated At (on PrestaShop)',
        readonly=True
    )
    newsletter = fields.Boolean('Newsletter')
    default_category_id = fields.Many2one(
        'prestashop.res.partner.category',
        'PrestaShop default category',
        help="This field is synchronized with the field "
        "'Default customer group' in PrestaShop."
    )
    birthday = fields.Date('Birthday')
    company = fields.Char('Company')
    prestashop_address_bind_ids = fields.One2many(
        'prestashop.address', 'openerp_id',
        string="PrestaShop Address Bindings"
    )

    _sql_constraints = [
        ('prestashop_uniq', 'unique(prestashop_id)',
         'A partner with the same ID on PrestaShop already exists for this '
         'website.'),
    ]


class prestashop_address(models.Model):
    _name = 'prestashop.address'
    _inherit = 'prestashop.binding'
    _inherits = {'res.partner': 'openerp_id'}

    _rec_name = 'backend_id'

    openerp_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade'
    )
    date_add = fields.Datetime(
        'Created At (on Prestashop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        'Updated At (on Prestashop)',
        readonly=True
    )
    prestashop_partner_id = fields.Many2one(
        'prestashop.res.partner',
        string='Prestashop Partner',
        required=True,
        ondelete='cascade'
    )
    backend_id = fields.Many2one(
        'prestashop.backend',
        related = 'prestashop_partner_id.backend_id',
        string='Prestashop Backend',
        readonly=True
    )
    vat_number = fields.Char('PrestaShop VAT')

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A partner address with the same ID on PrestaShop already exists.'),
    ]


class res_partner_category(models.Model):
    _inherit = 'res.partner.category'

    prestashop_bind_ids = fields.One2many(
        'prestashop.res.partner.category',
        'openerp_id',
        string='PrestaShop Bindings',
        readonly=True)


class PrestashopResPartnerCategory(models.Model):
    _name = 'prestashop.res.partner.category'
    _inherit = 'prestashop.binding'
    _inherits = {'res.partner.category': 'openerp_id'}

    openerp_id = fields.Many2one(
        'res.partner.category',
        string='Partner Category',
        required=True,
        ondelete='cascade'
    )
    date_add = fields.Datetime(
        'Created At (on Prestashop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        'Updated At (on Prestashop)',
        readonly=True
    )
        # TODO add prestashop shop when the field will be available in the api.
        # we have reported the bug for it
        # see http://forge.prestashop.com/browse/PSCFV-8284

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
         'A partner group with the same ID on PrestaShop already exists.'),
    ]
