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

    @api.depends('discount_percentage', 'original_price')
    def compute_list_price(self):
        """
            set list price with discounted price if discount percentage is set,
            otherwise, set original sales price as list price
        """
        for rec in self:
            if rec.discount_percentage:
                rec.list_price = rec.original_price * (1 - (rec.discount_percentage / 100))
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


    # for show discount price on list view of product, override below method
    def _get_sales_prices(self, pricelist, fiscal_position):
        """
            only updated condition for count base price when we have discount in our product is set - discount_percentage

            calculate base price based on original_price rather than list_price
        """
        if not self:
            return {}

        pricelist and pricelist.ensure_one()
        pricelist = pricelist or self.env['product.pricelist']
        currency = pricelist.currency_id or self.env.company.currency_id
        date = fields.Date.context_today(self)

        sales_prices = pricelist._get_products_price(self, 1.0)
        show_discount = pricelist and pricelist.discount_policy == 'without_discount'
        show_strike_price = self.env.user.has_group('website_sale.group_product_price_comparison')

        base_sales_prices = self._price_compute('list_price', currency=currency)

        res = {}
        for template in self:
            price_reduce = sales_prices[template.id]

            product_taxes = template.sudo().taxes_id._filter_taxes_by_company(self.env.company)
            taxes = fiscal_position.map_tax(product_taxes)

            base_price = None
            price_list_contains_template = currency.compare_amounts(price_reduce, base_sales_prices[template.id]) != 0

            if template.compare_list_price and show_strike_price:
                # The base_price becomes the compare list price and the price_reduce becomes the price
                base_price = template.compare_list_price
                if not price_list_contains_template:
                    price_reduce = base_sales_prices[template.id]

                if template.currency_id != currency:
                    base_price = template.currency_id._convert(
                        base_price,
                        currency,
                        self.env.company,
                        date,
                        round=False
                    )

            elif template.discount_percentage:
                # Compare_list_price are never tax included
                base_price = self._apply_taxes_to_price(
                    template.original_price, currency, product_taxes, taxes, template,
                )

            price_reduce = self._apply_taxes_to_price(
                price_reduce, currency, product_taxes, taxes, template,
            )

            template_price_vals = {
                'price_reduce': price_reduce,
            }
            if base_price:
                template_price_vals['base_price'] = base_price

            res[template.id] = template_price_vals

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

