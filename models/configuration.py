from odoo import models, fields, api


class typeOPD(models.Model):
    _name = 'opd.type'
    _inherit = 'mail.thread'
    _rec_name = 'type_of_opd'

    active = fields.Boolean(string='Active', default='1')
    type_of_opd = fields.Char('OPD Type', required=True)


# class HrExpenseSheet(models.Model):
#     _inherit = 'hr.expense.sheet'
#
#     x_studio_one2many_field_ex8zl = fields.Many2one('employee_id.x_studio_one2many_field_ex8zl', string='Dependents')

