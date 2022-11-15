from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_an_opd = fields.Boolean(string='Is an OPD?', default=False)
    is_limit_applicable = fields.Boolean(string='Is Limit Applicable?', default=False)
    opd_type = fields.Many2one('opd.type', string="OPD Type")
