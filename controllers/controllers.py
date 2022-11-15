# -*- coding: utf-8 -*-
# from odoo import http


# class RaynPayslip(http.Controller):
#     @http.route('/rayn_payslip/rayn_payslip', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rayn_payslip/rayn_payslip/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rayn_payslip.listing', {
#             'root': '/rayn_payslip/rayn_payslip',
#             'objects': http.request.env['rayn_payslip.rayn_payslip'].search([]),
#         })

#     @http.route('/rayn_payslip/rayn_payslip/objects/<model("rayn_payslip.rayn_payslip"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rayn_payslip.object', {
#             'object': obj
#         })
