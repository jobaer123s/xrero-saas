/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { session } from "@web/session";
// import rpc from "@web/legacy/js/core/rpc";
// import ajax from "@web/legacy/js/core/ajax";


publicWidget.registry.SaasUserModel = publicWidget.Widget.extend({
    selector: '.users_no_div',
    events: {
        'click #modal_target': '_onClickModalTarget',
    },

    init() {
        this._super(...arguments);
        // this.rpc = this.bindService("rpc");
        this.orm = this.bindService("orm");
    },
        
    _onClickModalTarget:function(){
        if (! session.user_id){
            alert("Please login First to Continue !");
            return;
        }
        var min_users = parseInt($('#min_user')).text;
        $('#new_min_user').attr('value',min_users);
        var product_id = parseInt($('.product_id').attr('value'));
        min_users = $('#new_min_user').val()
        $('#total_cost').text('');                
        // rpc.query({model: 'product.product',method: 'read',args: [[product_id],['user_cost']],})
        this.orm.read("product.product",[product_id], ['user_cost'])
        .then(function(data){
            var total_amount = min_users * (parseInt(data[0]['user_cost']));
            $('#total_cost').text(total_amount);
            $("#modify_min_users").modal("toggle");
        });            
    },
});

publicWidget.registry.SaasUserCount = publicWidget.Widget.extend({
    selector: '#modify_min_users',
    events: {
        'change #new_min_user': '_onChangeNewMinUser',
        'click #min_user_submit': '_onClickMinUserSubmit',
    },

    init() {
        this._super(...arguments);
        // this.rpc = this.bindService("rpc");
        this.orm = this.bindService("orm");
    },

    async _onChangeNewMinUser(){
        var min_users = parseInt($('#min_user_quantity').attr('value'));
        var max_users = parseInt($('#max_user_quantity').attr('value'));
        var new_user = parseInt($('#new_min_user').val());
        var product_id = parseInt($('.product_id').attr('value'));
        if (new_user < min_users){
            alert("User must be more than or equal to "+ min_users);
        }
        else if(new_user > max_users && max_users !== -1){
            alert("User must be less than or equal to "+ max_users);
        }else{
            // rpc.query({model: 'product.product',method: 'read',args: [[product_id],['user_cost']],})
            const data = await this.orm.read("product.product",[product_id], ['user_cost'])
            // .then(function(data){
                var total_amount = new_user * parseFloat(data[0]['user_cost']);
                $('#total_cost').text(total_amount);
            // });
        }
    },

    _onClickMinUserSubmit:function(){
        var min_users = parseInt($('#min_user_quantity').attr('value'));
        var max_users = parseInt($('#max_user_quantity').attr('value'));
        var new_user = parseInt($('#new_min_user').val());
        if (new_user < min_users){
            alert("User must be more than or equal to "+ min_users);
        }
        else if(new_user > max_users && max_users !== -1){
            alert("User must be less than or equal to "+ max_users);
        }else{
            $('#min_user').text(new_user);
            $('#number_of_user').attr('value',new_user);
            $('#modify_min_users').modal('hide');
        }
    },
});
