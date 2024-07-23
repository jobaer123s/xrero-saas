/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";


publicWidget.registry.ContractSubdomainOperations = publicWidget.Widget.extend({
    selector: '.contract_details_portal_page, #sub_domain_div, #add_custom_domain',
    events: {
        'click #sub_domain_span_1, #add_domain_icon_div': '_onClickAddDomain',
        // 'click #add_subdomain_is_ssl': '_onClickAddDomainIsSsl',
        'click #use_custom_domain': '_onClickUseCustomDomain',
        'click #btn_add_domain': '_onClickButtonAddDomain',
        'click .revoke_domain': '_onClickRevokeDomain',     //#portal_domain

    },

    init() {
        this._super(...arguments);
        // this.rpc = this.bindService("rpc");
        this.orm = this.bindService("orm");
    },

    _onClickAddDomain: function(ev){
        $("#add_custom_domain").modal("toggle");
        $("#ssl_note").hide();
    },

    _onClickUseCustomDomain: function(ev){
        if($("#use_custom_domain").prop("checked") == true){
            $("#base_url_text").hide();
            $("#ssl_note").show();
        }
        else{
            $("#ssl_note").hide();
            $("#base_url_text").show();
        }
    },

    _onClickButtonAddDomain: function(ev){
        var contract_id = $('#contract_id').attr('value');
        var domain_name = $('#add_subdomain_name').val();
        var use_seperate_domain = $("#use_custom_domain").prop("checked")
        var is_ssl = false;
        if($("#add_subdomain_is_ssl").prop("checked") == true){
            is_ssl = true
        }
        jsonrpc("/my/saas/contract/add/domain", {
            'contract_id':contract_id, 'domain_name':domain_name,'is_ssl':is_ssl,'use_seperate_domain':use_seperate_domain,
        }).then(function(vals){
            console.log(vals);
            if (vals['response']['status']){
                $("#add_custom_domain").modal("hide");
                $('#domain_tbody').replaceWith(vals['data']);
            }else{
                $('#domain_taken_warning').text(vals['response']['msg']);
                $('#domain_taken_warning').show();
            }
        });
    },

    _onClickRevokeDomain:function(ev){
        var answer = confirm("Are You Sure You want to Revoke this domain..?");
        if (answer == true){
            var domain_id = parseInt($(ev.currentTarget).attr('domain_id'));
            // rpc.query({model: 'custom.domain', method: 'revoke_subdomain_call', args: [domain_id],})
            this.orm.call("custom.domain", "revoke_subdomain_call", [domain_id])
            .then(function(url){
                location.href = url
            });
        }
    },
});
