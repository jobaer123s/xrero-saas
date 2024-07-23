/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
// import rpc from "@web/legacy/js/core/rpc";
// import ajax from "@web/legacy/js/core/ajax";
import { jsonrpc } from "@web/core/network/rpc_service";



publicWidget.registry.ContractSubdomainPage = publicWidget.Widget.extend({
    selector: '.domain_mapping_page_div',
    events: {

        'click .confirm_domain': '_onClickConfirmDomain',   //.subdomain_page_div
        'keyup keypress form': '_onKeyChangeForm',          //subdomain
    },

    init: function() {
        this._super(...arguments);
        this.ui = this.bindService("ui");
    },
    
    _onClickConfirmDomain:function(){
        var subdomain_name = $("#subdomain_name").val();
        var self = this;
        let pattern = /[ `!@#$%^&*()+\=\[\]{};':"\\|,.<>\/?~]/;
        if(pattern.test(subdomain_name)==true){
            $('#domain_error').show();
            $("#taken_error").hide();
            $("#taken_warning").hide();
            return false;
        }
        else{
            $('#domain_error').hide();
        }
        var contract_id = $("#contract_id").attr('value');
        if(subdomain_name.length == 0)
            $("#subdomain_name").css("border", "1px solid #ff1414")
        else{
            var domain_name = subdomain_name
            self.ui.block({ 
                message: 'Please wait! We are creating your SaaS Instance.',
            });
            jsonrpc("/mail/confirm_domain", {
                'domain_name': domain_name,
                'contract_id': contract_id,
            }).then(function (return_dict) {
                self.ui.unblock();
                if(return_dict.status == 1){
                    $("#taken_warning").show();
                }else if(return_dict.status == 3){
                    $("#taken_error").show();
                }else if(return_dict.status == 2){
                    $("#taken_warning").hide();
                    $("#taken_error").hide();
                    location.href='/client/domain-created/redirect?contract_id='+contract_id
                }
                else{
                    $("#taken_warning").hide();
                    $("#taken_error").hide();
                    $("#status_link").show();
                }
            });
        }
    },
    
    _onKeyChangeForm: function(e) {
        var keyCode = e.keyCode || e.which;
        if (keyCode === 13) { 
            e.preventDefault();
            return false;
        }
    },

});
