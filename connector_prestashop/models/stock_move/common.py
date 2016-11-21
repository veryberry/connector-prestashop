# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def update_prestashop_quantities(self):
        for move in self:
            move.product_id.update_prestashop_quantities()

    @api.model
    def get_stock_location_ids(self):
        warehouse_obj = self.env['stock.warehouse']
        warehouses = warehouse_obj.search([])
        location_ids = []
        for warehouse in warehouses:
            location_ids.append(warehouse.lot_stock_id.id)
        return location_ids

    @api.model
    def create(self, vals):
        stock = super(StockMove, self).create(vals)
        location_ids = self.get_stock_location_ids()
        if vals['location_id'] in location_ids:
            stock.update_prestashop_quantities()
        return stock

    @api.multi
    def action_cancel(self):
        res = super(StockMove, self).action_cancel()
        location_ids = self.get_stock_location_ids()
        for move in self:
            if move.location_id.id in location_ids:
                move.update_prestashop_quantities()
        return res

    @api.multi
    def action_done(self):
        res = super(StockMove, self).action_done()
        location_ids = self.get_stock_location_ids()
        for move in self:
            if move.location_dest_id.id in location_ids:
                move.update_prestashop_quantities()
        return res
