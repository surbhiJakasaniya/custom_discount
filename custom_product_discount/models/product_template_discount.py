from odoo import models, fields, api

class custom_product_discount(models.Model):
    _inherit = 'product.template'

    discount_percentage = fields.Float("Discount Percentage")
    original_price = fields.Float("Sales Original Price")
    list_price = fields.Float(compute="compute_list_price", store=True, string="Final Sales Price")

    def init(self):
        super().init()
        config_param_model = self.env['ir.config_parameter'].sudo()
        # set first time sales price value same as current price of product
        if not config_param_model.get_param('discount_migration_done'):
            self.env.cr.execute("UPDATE product_template SET original_price = list_price")
            config_param_model.set_param('discount_migration_done', True)

    @api.depends('discount_percentage', 'list_price')
    def compute_list_price(self):
        """
            set list price with discounted price if discount percentage is set,
            otherwise, set original sales price as list price
        """
        for rec in self:
            if rec.discount_percentage:
                rec.list_price = rec.list_price * (1 - (rec.discount_percentage / 100))
            else:
                rec.list_price = rec.original_price


    def _get_additionnal_combination_info(self, product_or_template, quantity, date, website):
        res = super()._get_additionnal_combination_info(product_or_template, quantity, date, website)
        if product_or_template.discount_percentage:
            # if discount set in our pro,duct, then update combination info for pricing
            if product_or_template.is_product_variant:
                res.update({
                    'price': product_or_template.lst_price,
                    'list_price': product_or_template.product_original_price,
                    'has_discounted_price': True,
                })
            else:
                res.update({
                    'price': product_or_template.list_price,
                    'list_price': product_or_template.original_price,
                    'has_discounted_price': True,
                })
        return res


class custom_product_product_discont(models.Model):
    _inherit = 'product.product'

    # to show original price on time of discount
    product_original_price = fields.Float("Original Price", compute="compute_original_price")

    @api.depends('original_price','price_extra')
    @api.depends_context('uom')
    def compute_original_price(self):
        to_uom = None
        if 'uom' in self._context:
            to_uom = self.env['uom.uom'].browse(self._context['uom'])

        for product in self:
            if to_uom:
                product_original_price = product.uom_id._compute_price(product.original_price, to_uom)
            else:
                product_original_price = product.original_price
            product.product_original_price = product_original_price + product.price_extra

