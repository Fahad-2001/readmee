from odoo import models, fields, api, _


class OpdPaymentRegister(models.TransientModel):
    _name = 'opd.payment.register'

    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type', 'in', ['cash', 'bank'])])
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal',
                                      domain=[('type', 'in', ['cash', 'bank'])],
                                      help="The payment method used when the expense is paid by the company.")
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method')
    partner_bank_id = fields.Many2one('res.partner.bank', string="Recipient Bank Account")
    total_amount = fields.Monetary("Amount", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today)
    communication = fields.Char(string='Memo')

    # == Payment difference fields ==
    payment_difference = fields.Monetary(
        compute='compute_payment_difference')
    payment_difference_handling = fields.Selection([
        ('open', 'Keep open'),
        ('reconcile', 'Mark as fully paid'),
    ], default='open', string="Payment Difference Handling")
    writeoff_account_id = fields.Many2one('account.account', string="Difference Account", copy=False)
    writeoff_label = fields.Char(string='Journal Item Label', default='Write-Off',
                                 help='Change label of the counterpart that will hold the payment difference')

    @api.onchange('total_amount')
    def compute_payment_difference(self):
        for wizard in self:
            difference_amount = self.env.context.get('default_total_amount') - wizard.total_amount
            wizard.payment_difference = difference_amount

    def action_create_opd_payments(self):
        print("HELLLO ITS PAYMENT")
        vals_form = {
            'journal_id': self.journal_id.id,
            'amount': self.total_amount,
            'date': self.payment_date,
            'ref': self.communication,
        }
        print("FORM VALUES", vals_form)
        account_payment = self.env['account.payment'].create(vals_form)
        account_payment.action_post()
        account_payment.payment_type = 'outbound'
        rayn_opd = self.env['rayn.opd'].browse(self.env.context.get('active_id')).action_done()
        return account_payment, rayn_opd
