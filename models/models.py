from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.addons.account.models.account_move import PAYMENT_STATE_SELECTION


class RaynOPD(models.Model):
    _name = "rayn.opd"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "OPD Form"

    @api.model
    def _default_employee_id(self):
        return self.env.user.employee_id

    @api.model
    def _default_journal_id(self):
        default_company_id = self.default_get(['company_id'])['company_id']
        journal = self.env['account.journal'].search(
            [('type', '=', 'purchase'), ('company_id', '=', default_company_id)], limit=1)
        return journal.id

    @api.model
    def _get_employee_id_domain(self):
        res = [('id', '=', 0)]  # Nothing accepted by domain, by default
        if self.user_has_groups('hr_expense.group_hr_expense_user') or self.user_has_groups(
                'account.group_account_user'):
            res = "['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
        # Then, domain accepts everything
        elif self.user_has_groups('hr_expense.group_hr_expense_team_approver') and self.env.user.employee_ids:
            user = self.env.user
            employee = self.env.user.employee_id
            res = [
                '|', '|', '|',
                ('department_id.manager_id', '=', employee.id),
                ('parent_id', '=', employee.id),
                ('id', '=', employee.id),
                ('expense_manager_id', '=', user.id),
                '|', ('company_id', '=', False), ('company_id', '=', employee.company_id.id),
            ]
        elif self.env.user.employee_id:
            employee = self.env.user.employee_id
            res = [('id', '=', employee.id), '|', ('company_id', '=', False),
                   ('company_id', '=', employee.company_id.id)]
        return res

    name = fields.Char(required=True)
    product_id = fields.Many2one(related="expense_line_ids.product_id", string='Product', store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 states={'draft': [('readonly', False)], 'refused': [('readonly', False)]},
                                 default=lambda self: self.env.company)
    total_amount = fields.Monetary("Total Amount", compute='_compute_total_amount', store=True,
                                   currency_field='currency_id', tracking=True, readonly=True)
    unit_amount = fields.Float("Unit Price", compute='_compute_from_product_id_company_id', store=True, required=True,
                               copy=True,
                               states={'draft': [('readonly', False)], 'reported': [('readonly', False)],
                                       'approved': [('readonly', False)], 'refused': [('readonly', False)]},
                               digits='Product Price')
    quantity = fields.Float(required=True, readonly=True,
                            states={'draft': [('readonly', False)], 'reported': [('readonly', False)],
                                    'approved': [('readonly', False)], 'refused': [('readonly', False)]},
                            digits='Product Unit of Measure', default=1)
    tax_ids = fields.Many2many('account.tax',
                               string='Taxes',
                               help="The taxes should be \"Included In Price\"")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=False, store=True,
                                  states={'reported': [('readonly', True)], 'approved': [('readonly', True)],
                                          'Done': [('readonly', True)]}, compute='_compute_currency_id',
                                  default=lambda self: self.env.company.currency_id)
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', compute='_compute_from_product_id_company_id',
                                     store=True, copy=True,
                                     domain="[('category_id', '=', product_uom_category_id)]")
    unit_amount = fields.Float("Unit Price", compute='_compute_from_product_id_company_id', store=True, required=True,
                               copy=True, digits='Product Price')

    account_id = fields.Many2one(related="expense_line_ids.product_id.property_account_expense_id", string='Account',
                                 help="An expense account is expected")
    project_id = fields.Many2one('project.project', string='Project', required=False)

    analytic_account_id = fields.Many2one(related="project_id.analytic_account_id", string='Analytic Account',
                                          check_company=True)
    # analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', check_company=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags',
                                        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    employee_id = fields.Many2one('hr.employee', compute='_compute_employee_id', string="Employee",
                                  store=True, required=True, readonly=False, tracking=True,
                                  default=_default_employee_id, domain=lambda self: self._get_employee_id_domain(),
                                  check_company=True)

    journal_id = fields.Many2one('account.journal', string='Expense Journal',
                                 states={'Done': [('readonly', True)], 'Posted': [('readonly', True)]},
                                 domain="[('type', '=', 'purchase'), ('company_id', '=', company_id)]",
                                 default=_default_journal_id, help="The journal used when the expense is done.")

    reference = fields.Char("Bill Reference")
    bill_date = fields.Date(string='Date of Bill', default=fields.Date.context_today)
    expense_for = fields.Selection(
        string='Expense For',
        selection=[('Self', 'Self'),
                   ('Spouse', 'Spouse'),
                   ('Children', 'Children')],
        required=True, default='Self')
    state = fields.Selection(
        string='State',
        selection=[('Draft', 'Draft'),
                   ('Submitted', 'Submitted'),
                   ('Approved', 'Approved'),
                   ('Rejected', 'Rejected'),
                   ('Posted', 'Posted'),
                   ('Done', 'Done'),
                   ], default="Draft")
    expense_line_ids = fields.One2many("rayn.opd.line", 'opd_id', string="Expense Lines")
    # amount_residual = fields.Monetary(string='Amount Due', compute='_compute_amount_residual')
    account_move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='restrict', copy=False,
                                      readonly=True)
    payment_state = fields.Selection(selection=PAYMENT_STATE_SELECTION, string="Payment Status",
                                     store=True, readonly=True, copy=False, tracking=True,
                                     compute='_compute_payment_state')

    # remaining_balance = fields.Float(compute='remaining_dental_balance')

    # @api.depends("total_amount")
    # def remaining_dental_balance(self):
    #     for rec in self:
    #         rec.total_amount = rec.total_amount - 50000

    # @api.depends("account_move_id.line_ids")
    # def _compute_amount_residual(self):
    #     for expense in self:
    #         if not expense:
    #             expense.amount_residual = expense.total_amount
    #             continue
    #         if not expense.currency_id or expense.currency_id == expense.company_id.currency_id:
    #             residual_field = 'amount_residual'
    #         else:
    #             residual_field = 'amount_residual_currency'
    #         payment_term_lines = expense.account_move_id.sudo().line_ids \
    #             .filtered(lambda line: line.expense_id == self)
    #         expense.amount_residual = -sum(payment_term_lines.mapped(residual_field))

    @api.depends('account_move_id.payment_state')
    def _compute_payment_state(self):
        for sheet in self:
            sheet.payment_state = sheet.account_move_id.payment_state or 'not_paid'

    @api.model
    def create(self, vals):
        res = super(RaynOPD, self).create(vals)
        current_records = self.env['rayn.opd']
        # print("current_records", current_records)
        if type(' ') == type(vals['bill_date']):
            current_bill_date_year = datetime.strptime(vals['bill_date'], "%Y-%M-%d").strftime("%Y")
        else:
            current_bill_date_year = vals['bill_date'].strftime("%Y")
        # print("current_bill_date_year", current_bill_date_year)
        dental_records = self.env['rayn.opd.line'].search([('product_id.is_limit_applicable', '=', True)]).mapped(
            'opd_id')
        dental_records = dental_records.filtered(lambda opd: opd.employee_id.id == vals['employee_id'])
        # print("dental_records", dental_records)
        current_year_amount = 0
        # print("current_year_amount", current_year_amount)
        for dental_record in dental_records:
            # print("dentallllllllllllllllllllllllll_record", dental_record)
            if not dental_record.bill_date:
                raise ValidationError("Plz set bill date on some record")
            dental_record_year = dental_record.bill_date.strftime("%Y")
            # print("dental_record_yearrrrrrrrrrrrrrrrrr", dental_record_year)
            if dental_record_year == current_bill_date_year:
                current_year_amount += dental_record.total_amount
                # print("ccccccccccccccccccccccurrent_year_amount", current_year_amount)
                # dental_records.expense_line_ids.product_id.standard_price
            if current_year_amount >= 50000:
                raise ValidationError(_("Amount for Dental Treatment exceeded for current year."))
        return res

    def post_journal_entries(self):
        vals_form = {
            'ref': self.name,
            'date': self.bill_date,
            'journal_id': self.journal_id.id,
        }
        print("FORM VALUES", vals_form)
        for rec in self:
            # Validation for payable account
            if not rec.expense_line_ids.product_id.property_account_expense_id:
                raise ValidationError(_("Expense Account on Product has to be defined."))
            lines_vals = []
            # Expense debit lines
            for line in self.expense_line_ids:
                lines_vals.append((0, 0, {
                    'account_id': line.account_id.id,
                    'name': rec.employee_id.name,
                    'analytic_tag_ids': rec.analytic_tag_ids.ids,
                    'debit': line.amount,

                }))
            # Expense Payable Credit line
            lines_vals.append((0, 0, {
                'account_id': rec.employee_id.address_home_id.property_account_payable_id.id,
                'name': rec.employee_id.name,
                'analytic_tag_ids': rec.analytic_tag_ids.ids,
                'credit': rec.total_amount,
            }))
        account_move = self.env['account.move'].create(vals_form)
        account_move.write({'line_ids': lines_vals})
        account_move.action_post()
        self.state = "Posted"
        return account_move

    def action_open_account_move(self):
        self.ensure_one()
        return {
            'name': self.account_id.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('account.view_move_tree').id,
            'res_model': 'account.move',
            'res_id': self.account_id.id,
            'domain': [('ref', '=', self.name)],
        }

    @api.depends('quantity', 'unit_amount', 'tax_ids', 'currency_id')
    def _compute_amount(self):
        for expense in self:
            if expense.unit_amount:
                expense.untaxed_amount = expense.unit_amount * expense.quantity
                taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity,
                                                    expense.product_id, expense.employee_id.user_id.partner_id)
                expense.total_amount = taxes.get('total_included')

    @api.depends('product_id', 'company_id')
    def _compute_from_product_id_company_id(self):
        for expense in self.filtered('product_id'):
            expense = expense.with_company(expense.company_id)
            expense.name = expense.name or expense.product_id.display_name
            if not expense.attachment_number or (expense.attachment_number and not expense.unit_amount):
                expense.unit_amount = expense.product_id.price_compute('standard_price')[expense.product_id.id]
            expense.product_uom_id = expense.product_id.uom_id
            expense.tax_ids = expense.product_id.supplier_taxes_id.filtered(
                lambda tax: tax.company_id == expense.company_id)  # taxes only from the same company
            account = expense.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                expense.account_id = account

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'hr.expense'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense._origin.id, 0)

    @api.depends('company_id')
    def _compute_employee_id(self):
        if not self.env.context.get('default_employee_id'):
            for expense in self:
                expense.employee_id = self.env.user.with_company(expense.company_id).employee_id

    @api.onchange('expense_line_ids')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = 0
            for line in rec.expense_line_ids:
                if line.amount:
                    rec.total_amount += line.amount
                else:
                    rec.total_amount = 0

    def action_draft(self):
        for rec in self:
            rec.state = 'Draft'

    def action_submit(self):
        for rec in self:
            rec.state = 'Submitted'

    def action_approve(self):
        for rec in self:
            rec.state = 'Approved'

    def action_reject(self):
        for rec in self:
            rec.state = 'Rejected'

    def action_done(self):
        for rec in self:
            rec.state = 'Done'


class raynOpdLines(models.Model):
    _name = "rayn.opd.line"

    opd_id = fields.Many2one('rayn.opd', string="OPD Reference")
    expense_type = fields.Many2one('opd.type', string='Expense Type')
    product_id = fields.Many2one('product.product', string='Product', tracking=True,
                                 domain=[('is_an_opd', '=', True)], store=True)
    account_id = fields.Many2one(related="product_id.property_account_expense_id", string='Account',
                                 help="An expense account is expected")
    opd_type = fields.Many2one(related="product_id.opd_type", string='Type(s)')
    account_move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='restrict', copy=False,
                                      readonly=True)
    spouse_name = fields.Char(string='Patient Name', related="opd_id.employee_id.x_studio_spouse_name")
    amount = fields.Float(string="Amount (PKR)")
    dependant_id = fields.Many2one('x_dependant', string="Patient Name",
                                   domain="[('x_studio_many2one_field_f1ew5', '=', parent.employee_id)]")
    bill = fields.Binary(string='Bill', copy=False, required=True)
    prescription = fields.Binary(string='Prescription', copy=False, required=True)
