/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
// import rpc from "@web/legacy/js/core/rpc";
// import ajax from "@web/legacy/js/core/ajax";
import { jsonrpc } from "@web/core/network/rpc_service";


var apps = new Array();
$('#error_message').hide();
$("a.nav-link[href='/custom/plan']").addClass('text-info');

publicWidget.registry.CustomPlanUpdateApp = publicWidget.Widget.extend({
    selector: '#add_apps_button, .modal-content',

    // var apps = new Array();
    // $('#error_message').hide();
    // $("a.nav-link[href='/custom/plan']").addClass('text-info');
    events: {
        'click #add_apps_icon_div, #add_app_span_1': '_onAddContractApp',
        'click  #add_apps_submit' : '_onAddAppSubmit',
        'click  .apps_to_select_button' : '_onPortalAppSelectButton',
        'click  .apps_selected_button' : '_onPortalAppSelectedButton',
    },

    init() {
        this._super(...arguments);
        // this.rpc = this.bindService("rpc");
        this.orm = this.bindService("orm");
    },

    async _onAddContractApp(){
        var contract_id = parseInt($('#add_apps_submit').attr('value'));
        await this.orm.call(
            'saas.contract',
            'get_module',
            [contract_id],
        )
        .then(function(data){
            if (data){
                apps.length = 0;
                $('.apps_to_select_button').css('display', 'inline');
                $('.apps_selected_button').css('display', 'none');
                $('.apps_to_add_data_row').css('background', '#FFFFFF');
                $("#add_apps").modal("toggle");
            }
        });
    },

    _onAddAppSubmit : function(){
        if (apps.length == 0){
            alert('Please Select Atleast One App to continue !')
            return
        }
        var contract_id = parseInt($('#add_apps_submit').attr('value'));
        // rpc.query({
            //     model: 'saas.contract',
            //     method: 'add_apps',
            //     args: [apps, contract_id],
            // })
            // .then(function(data){
                //     $('#add_apps').modal('hide');
                //     location.href='/my/saas/contract/'+contract_id+'?access_token='+data
                // });
        
        jsonrpc("/my/saas/contract/add/apps", {
            'apps': apps, 'contract_id':contract_id,
        }).then(function(data){
            // alert("after ajax add_apps_submit");
            $('#add_apps').modal('hide');
            $('#apps_tbody').replaceWith(data);
        });
    },

    _onPortalAppSelectButton : function(ev){
        var technical_name = $(ev.currentTarget).closest('.apps_to_add_img_row').find('.apps_to_add_tech_name').text();
        apps.push(technical_name);
        $(ev.currentTarget).closest('.apps_to_add_data_row').css('background', 'rgba(141, 255, 87, 0.2)');
        $(ev.currentTarget).closest('.apps_to_add_img_row').find('.apps_selected_button').css('display', 'inline');
        $(ev.currentTarget).closest('.apps_to_add_img_row').find('.apps_to_select_button').css('display', 'none');
    },

    _onPortalAppSelectedButton : function(){
        var technical_name = $(ev.currentTarget).closest('.apps_to_add_img_row').find('.apps_to_add_tech_name').text();
        apps.splice($.inArray(technical_name, apps), 1);
        $(ev.currentTarget).closest('.apps_to_add_data_row').css('background', '#FFFFFF');
        $(ev.currentTarget).closest('.apps_to_add_img_row').find('.apps_selected_button').css('display', 'none');
        $(ev.currentTarget).closest('.apps_to_add_img_row').find('.apps_to_select_button').css('display', 'inline');
    },
});
