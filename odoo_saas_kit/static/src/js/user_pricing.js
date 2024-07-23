/** @odoo-module **/

import { WebsiteSale } from '@website_sale/js/website_sale';

WebsiteSale.include({

    /**
     * Adds the number_of_user value for saas users.
     * @override
     */
    _submitForm: function () {
        const params = this.rootProduct;
        const $product = $('#product_detail');
        const productTrackingInfo = $product.data('product-tracking-info');
        params.number_of_user = this.$form.find('#number_of_user').val();            
        if (productTrackingInfo) {
            productTrackingInfo.quantity = params.quantity;
            $product.trigger('add_to_cart_event', [productTrackingInfo]);
        }

        params.add_qty = params.quantity;
        params.product_custom_attribute_values = JSON.stringify(params.product_custom_attribute_values);
        params.no_variant_attribute_values = JSON.stringify(params.no_variant_attribute_values);
        delete params.quantity;
        return this.addToCart(params);
    },
});
