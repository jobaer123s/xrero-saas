/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
// import rpc from "@web/legacy/js/core/rpc";
// import ajax from "@web/legacy/js/core/ajax";
import { jsonrpc } from "@web/core/network/rpc_service";



publicWidget.registry.TrialContractPay = publicWidget.Widget.extend({
    selector: '#portal_my_saas_contracts',
    events: {
        'click .pay_for_trial': '_onClickPayForTrial',

    },

    _onClickPayForTrial: function(ev){
       
        var contract_id = $(ev.currentTarget).attr('value');
    }
});

publicWidget.registry.TrialContractPayModel = publicWidget.Widget.extend({
    selector: '#pay_now_modal',
    events: {
        'click #button_submit': '_onClickButtonSubmit',

    },

    _onClickButtonSubmit: function(ev){
        var radio_1 = $('#radio_1').is(':checked');
        var radio_2 = $('#radio_2').is(':checked');
        var contract_id = $("#contract_id").attr('value');
        var contract_id = $(ev.currentTarget).attr('value');
        if (! contract_id){
            return
        }
        if (radio_1){
            var new_contract = false;
            jsonrpc('/saa/trial/pay_now', {
                contract_id: parseInt(contract_id),
                from_trial: true,
                new_contract: new_contract,
            }).then(function(){
                location.href="/shop/cart";
            });
        }
        else if(radio_2){
            var new_contract = true;
            jsonrpc('/saa/trial/pay_now', {
                contract_id: parseInt(contract_id),
                from_trial: true,
                new_contract: new_contract,
            }).then(function(){
                location.href="/shop/cart";
            });
        }
    }

});
