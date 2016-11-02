from openerp import api, fields, models


class MailMessage(models.Model):
    _inherit = 'mail.message'

    prestashop_bind_ids = fields.One2many(
        'prestashop.mail.message',
        'openerp_id',
        string="Prestashop Bindings"
    )


class PrestashopMailMessage(models.Model):
    _name = "prestashop.mail.message"
    _inherit = "prestashop.binding"
    _inherits = {'mail.message': 'openerp_id'}

    openerp_id = fields.Many2one(
        'mail.message',
        string="Message",
        required=True,
        ondelete='cascade'
    )
