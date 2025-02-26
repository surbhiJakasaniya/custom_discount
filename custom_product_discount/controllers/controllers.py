# -*- coding: utf-8 -*-
# from odoo import http


# class CustomProductDiscount(http.Controller):
#     @http.route('/custom_product_discount/custom_product_discount', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_product_discount/custom_product_discount/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_product_discount.listing', {
#             'root': '/custom_product_discount/custom_product_discount',
#             'objects': http.request.env['custom_product_discount.custom_product_discount'].search([]),
#         })

#     @http.route('/custom_product_discount/custom_product_discount/objects/<model("custom_product_discount.custom_product_discount"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_product_discount.object', {
#             'object': obj
#         })

