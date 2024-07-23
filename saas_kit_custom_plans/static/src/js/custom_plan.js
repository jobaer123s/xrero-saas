/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
// import rpc from "@web/legacy/js/core/rpc";
// import ajax from "@web/legacy/js/core/ajax";
import { jsonrpc } from "@web/core/network/rpc_service";
import { session } from "@web/session";

// var session = require('web.session');
// var rpc = require('web.rpc');
// var ajax = require('web.ajax');
var number = 1;
// var publicWidget = require('web.public.widget');
var total_app_value_span = 0;
var final_cost_value_span = 0;
var users_price = 0;
var prev_cycle = 'Monthly';
var remove_button = false;
var apps = new Array();
var temp_apps = new Array();
var price_dict = {};
var max_users = 0;
var max_no_users=false;
var annual_discount= false;
var discount_percent= 0;
var discount_value_span= 0;
    
publicWidget.registry.CustomPlan = publicWidget.Widget.extend({
    selector: '.custom_plan_section',

    events: {
        'click #toggle_input': '_onToggleCategoryView',
        'click  .select_button' : '_onSelectApp',
        'mouseenter .selected_button' : '_onEnterSelectedButton',
        'mouseleave .remove_button' : '_onLeaveRemoveButton',      
        'click  .remove_button' : '_onClickRemoveButton',
        'click   #view_more_apps': '_onClickMoreApps',
        'click  .remove_app_button': '_onClickRemoveAppButton',
        'change #number_of_users' : '_onChangeUsers',
        'click #buy_now' : '_onClickBuyNow',
        'click .version_button' : '_onSelectVersion',
        'click .billing_cycle' : '_onSelectBilling',
    },

    init() {
        this._super(...arguments);
        // this.rpc = this.bindService("rpc");
        this.orm = this.bindService("orm");
    },

    setup() {
        super.setup(...arguments);
        var self = this;
        this.orm = useService("orm");
    },

    _return_apps_data : function(ev){
        return apps;
    },

    _return_apps_value : function(ev){
        return total_app_value_span;
    },

    _get_price_dict : function(ev){
        return price_dict;
    },

    _check_discount : function(){
        if (annual_discount){
            if (number == 12){
                discount_value_span= (final_cost_value_span * (discount_percent/100.00));
                console.log(discount_value_span);
                final_cost_value_span=final_cost_value_span-discount_value_span;
            }
            else{
                discount_value_span=0;
            }
        }
        return true;
    },

    _check_if_discounted : function(cost){
        var discounted_cost;
        if (annual_discount && (number == 12)){
            discounted_cost= cost-(cost*(discount_percent/100));
            return discounted_cost;
        }
        else return cost;

    },

    _toggle_selected_apps: function () {
        for (var app in apps) {
            app = "#" + apps[app] + '_main';
            $(app).find('.select_button').hide()
            $(app).find('.select_button').css('display', 'none');
            $(app).find('.selected_button').css('display', 'inline');
            $(app).css({ 'background-color': '#3AADAA;', 'border': '1px solid #3AADAA' });
            $(app).find('.app_name').css({ 'color': '#FFFFFF;' });
            $(app).find('.span_price').css({ 'color': '#FFFFFF;' });
            $(app).find('.price').css({ 'color': '#FFFFFF;' });
        }
    },


    _onToggleCategoryView: function (ev) {
        $('#error_message').hide();
        var self = this;
        var version_code = $('#dropdownmenu2').attr('data-code');
        if ($('input').is(':checked')){
            $.get("/show/categ/view", { 'version_code': version_code
            }).then(function(data){
                $('#normal_view_main_div').replaceWith(data);
                self._toggle_selected_apps();
            });
        }
        else{
            $.get("/show/normal/view", { 'version_code': version_code
            }).then(function(data){ 
                $('#category_view_main_div').replaceWith(data);
                self._toggle_selected_apps();
            });
        }
    },

    _onSelectVersion : function(event){
        $('#error_message').hide();
        var version_name = $(event.target).text();
        var version_code = $(event.target).attr('data-code');
        $('#dropdownmenu2').text(version_name);
        $('#dropdownmenu2').attr('data-code', version_code);
        
        if ($('#toggle_input').is(':checked')){
            console.log("IN redirect cat ver");
            jsonrpc("/custom/version/categ", {
                'version_code': version_code,
            }).then(function(data){
                $('#category_view_main_div').replaceWith(data);
            });
        }

        else{
            console.log("IN redirect normal ver");
            jsonrpc("/custom/version/normal", {
                'version_code': version_code,
            }).then(function(data){
                $('#normal_view_main_div').replaceWith(data);
            });
        }
        $.get("/show/selected/apps/view", {
        }).then(function (data) {
            $('#right_block').replaceWith(data);
            apps.length = 0;
            total_app_value_span = 0;
            final_cost_value_span = 0;
            users_price = 0;
        });


    },
    
    update_costing_view : function(price_1){
        var self=this;
        total_app_value_span = total_app_value_span + price_1;
        final_cost_value_span = total_app_value_span + users_price;

        self._check_discount();

        $('#total_app_value_span').text(total_app_value_span.toString()+' ');
        $('#discount_value_span').text(discount_value_span.toString()+' ');
        $('#final_cost_value_span').text(final_cost_value_span.toString()+' ');
        $('#pay_now_value_span').text(final_cost_value_span.toString()+' ');
    },

    _onSelectBilling : function(event){
        var self=this;
        var billing_type = $(event.target).text();
        $('#dropdownmenu3').text(billing_type);
        this.orm.call('saas.odoo.version','get_default_saas_values',[])
        .then(function(data){
            if (billing_type == 'Monthly'){
                number = 1;
                if (prev_cycle == 'Yearly'){
                    total_app_value_span = total_app_value_span / 12;
                }
                prev_cycle = 'Monthly';
                $('#discount').css('display', 'none');
            }
            else{
                number = 12;
                annual_discount=data['annual_discount'];
                discount_percent=data['discount_percent'];    
                if (prev_cycle == 'Monthly'){
                    total_app_value_span = total_app_value_span * 12;
                }
                prev_cycle = 'Yearly';
                $('#discount').css('display', 'flex');
            }
            if (data['is_users']){
                var user_cost = data['user_cost'];
                var users = $('#number_of_users').val();
                if (data['is_free_users']){
                    users_price = (users - data['free_users']) * user_cost;
                    if (users_price < 0){
                        users_price = 0;
                        }
                    }else{
                        users_price = users * user_cost;
                    }
                    users_price = users_price * number;    
                    $('#user_price_span').text(user_cost.toString()+' ');
                    $('#total_users_value_span').text(users_price.toString()+' ');    
                }
            
            final_cost_value_span = total_app_value_span + users_price;
            self._check_discount();
            $('#total_app_value_span').text(total_app_value_span.toString()+' ');
            $('#discount_value_span').text(discount_value_span.toString()+' ');
            $('#final_cost_value_span').text(final_cost_value_span.toString()+' ');
            $('#pay_now_value_span').text(final_cost_value_span.toString()+' ');
            }
        );
    },

    change_app_card: function(ev){
        $(ev.currentTarget).closest('.select_button_div').find('.select_button').css('display', 'none');
        $(ev.currentTarget).closest('.select_button_div').find('.selected_button').css('display', 'inline');
        $(ev.currentTarget).closest('.app_card').css({'background-color': '#3AADAA;', 'border': '1px solid #3AADAA'});            
        $(ev.currentTarget).closest('.col-8').find('.app_name').css({'color': '#FFFFFF;'});            
        $(ev.currentTarget).closest('.col-8').find('.span_price').css({'color': '#FFFFFF;'});       
        $(ev.currentTarget).closest('.col-8').find('.price').css({'color': '#FFFFFF;'});
    },

    set_total_count : function(ev){
        var total_count = $('#total_apps_count').text();
        total_count = parseInt(total_count);
        total_count = total_count + 1;
        if (total_count < 10){ 
            $('#total_apps_count').text('0'+total_count.toString());
        }else{
            $('#total_apps_count').text(total_count.toString());
        }
    },

    update_side_portal_height : function(increase){
        var height = $('#line_complete').css('height');
        height = height.split('p');
        if (height){
            height = parseInt(height[0]);
            if (increase){
                height = height + 37;
            }else{
                height = height - 37;
            }
            $('#line_complete').css('height', height.toString()+'px');
        }
    },

    get_user_price : function(data){
        var user_cost = data['user_cost'];
        var users = $('#number_of_users').val();
        if (data['is_free_users']){
            users_price = (users - data['free_users']) * user_cost;
            if (users_price < 0){
                users_price = 0;
            }
        }else{
            users_price = users * user_cost;
        }
        users_price = users_price * number;
    },


    add_side_bar_app : function(technical_name, name, price, currency){
        $('#test_apps_detail_div').prepend('<div class="apps_name_head d-flex" id="'+technical_name+'">'+
            '<div class="nodes">'+
            '</div>'+
            '<div class="node_head">'+
            '</div>'+ 
            '<div class="app_name_detail">'+name+'</div>'+
            '<div class="app_price"> '+price+' '+currency+
            '</div>'+
            '<div class="remove_button_div">'+
                '<button class="remove_app_button">'+
                    'REMOVE'+
                '</button>'+
            '</div>'+
        '</div>');
    },

    // _onSelectApp :async function(ev){
    async _onSelectApp(ev){
        ev.preventDefault();
        $('#error_message').hide();
        var self = this;
        if (! session.user_id){
            alert("Please login First to Continue !");
            return;
        }

        var technical_name = $(ev.currentTarget).closest('.app_card').find('.app_tech_name').text();
        var name = $(ev.currentTarget).closest('.app_card').find('span.app_name').text();
        var currency = $('#currency').text();
        var odoo_version_code = $('#dropdownmenu2').attr('data-code')

        // orm.call({
        //     model: 'saas.module',
        //     method: 'search_read',
        //     args: [[['technical_name', '=', technical_name],['odoo_version_id.code', '=' ,odoo_version_code]], ['price']],
        // })
        const data = await this.orm.call('saas.module', 'search_read',[],{
            fields: ['price'],
            domain: [['technical_name', '=', technical_name],['odoo_version_id.code', '=' ,odoo_version_code]]
        });
        // .then(function(data){
            // var price = parseInt(data[0]['price']);
            var price = data[0]['price'];
            price_dict[technical_name] = price
            var price_1 = price * number;
            await this.orm.call(
                'saas.odoo.version',
                'get_default_saas_values',
                [],
            )
            .then(function(data){
                if (data['is_users']){
                    self.get_user_price(data);
                }

                $('#apps_complete_details').hide();
                self.set_total_count(ev);
                self.change_app_card(ev);
                self.update_side_portal_height(true);        
                self.update_costing_view(price_1);
                self.add_side_bar_app(technical_name, name, price, currency);
                apps.push(technical_name);
                console.log(price_dict);
            });
        // });
    },

    _onEnterSelectedButton : function(ev){
        $(ev.currentTarget).closest('.select_button_div').find('.selected_button').css('display', 'none');
        $(ev.currentTarget).closest('.select_button_div').find('.remove_button').css('display', 'inline');
    },

    _onLeaveRemoveButton : function(ev){
        if (remove_button){
            remove_button = false;
        }else{
            $(ev.currentTarget).closest('.select_button_div').find('.selected_button').css('display', 'inline');
            $(ev.currentTarget).closest('.select_button_div').find('.remove_button').css('display', 'none');
        }
    },

    decrease_app_count : function(ev){
        var total_count = $('#total_apps_count').text();
        total_count = parseInt(total_count);
        total_count = total_count - 1;
        if (total_count < 10){ 
            $('#total_apps_count').text('0'+total_count.toString());
        }else{
            $('#total_apps_count').text(total_count.toString());
        }
    },

    remote_from_side_panel : function(ev){
        $(ev.currentTarget).closest('.select_button_div').find('.selected_button').css('display', 'none');
        $(ev.currentTarget).closest('.select_button_div').find('.remove_button').css('display', 'none');
        $(ev.currentTarget).closest('.select_button_div').find('.selected_button').css('display', 'none');
        $(ev.currentTarget).closest('.select_button_div').find('.select_button').css('display', 'inline');
        $(ev.currentTarget).closest('.app_card').css({'background-color': '#FFFFFF;', 'border': '1px solid #CCCCC'});
        $(ev.currentTarget).closest('.app_card').css('border', '1px solid #CCCCCC');
        $(ev.currentTarget).closest('.col-8').find('.app_name').css({'color': '#000000;'});          
        $(ev.currentTarget).closest('.col-8').find('.price').css({'color': '#000000;'});
        $(ev.currentTarget).closest('.col-8').find('.span_price').css({'color': '#000000;'});
    },

    _onClickRemoveButton : function(ev){
        $('#error_message').hide();
        var self = this;
        self.decrease_app_count()
        self.remote_from_side_panel(ev)
        remove_button = true;
        var technical_name = $(ev.currentTarget).closest('.app_card').find('.app_tech_name').text();
        $('#'+technical_name).remove();
        $('#'+technical_name+'_node').remove();
        
        self.update_side_portal_height(false)
        
        var price = price_dict[technical_name]
        price = price * number;
        total_app_value_span = total_app_value_span - price;

        final_cost_value_span = total_app_value_span + users_price;
        self._check_discount();
        $('#total_app_value_span').text(total_app_value_span.toString()+' ');
        $('#discount_value_span').text(discount_value_span.toString()+' ');
        $('#final_cost_value_span').text(final_cost_value_span.toString()+' ');
        $('#pay_now_value_span').text(final_cost_value_span.toString()+' ');

        apps.splice($.inArray(technical_name, apps), 1);

    },

    remove_app_card : function(technical_name){
        $('#'+technical_name+'_node').remove();
        $('#'+technical_name).remove();
        $('#'+technical_name+'_main').find();
        $('#'+technical_name+'_main').find('.selected_button').css('display', 'none');
        $('#'+technical_name+'_main').find('.remove_button').css('display', 'none');
        $('#'+technical_name+'_main').find('.selected_button').css('display', 'none');
        $('#'+technical_name+'_main').find('.select_button').css('display', 'inline');
        $('#'+technical_name+'_main').css({'background-color': '#FFFFFF;', 'border': '1px solid #CCCCC'});
        $('#'+technical_name+'_main').css('border', '1px solid #CCCCCC');
        $('#'+technical_name+'_main').find('.app_name').css({'color': '#000000;'});
        $('#'+technical_name+'_main').find('.price').css({'color': '#000000;'});
        $('#'+technical_name+'_main').find('.span_price').css({'color': '#000000;'});
    },

    _onClickRemoveAppButton : function(ev){
        var self = this;
        self.decrease_app_count();
        var technical_name = $(ev.currentTarget).closest('.apps_name_head').attr('id');
        self.remove_app_card(technical_name)
        self.update_side_portal_height(false)
        
        var price = price_dict[technical_name]
        
        price = price * number;
        total_app_value_span = total_app_value_span - price;

        final_cost_value_span = total_app_value_span + users_price;
        self._check_discount();
        $('#total_app_value_span').text(total_app_value_span.toString()+' ');
        $('#discount_value_span').text(discount_value_span.toString()+' ');
        $('#final_cost_value_span').text(final_cost_value_span.toString()+' ');
        $('#pay_now_value_span').text(final_cost_value_span.toString()+' ');
        
        apps.splice($.inArray(technical_name, apps), 1);
    },

    _onClickMoreApps : function(ev){
        $('#apps_details').attr('style', 'visiblity: hidden');
        $('#apps_details').attr('style', 'height: 0px');
        $('#apps_complete_details').attr('style', 'visiblity: visible');
        $('#apps_complete_details').attr('style', 'height: auto');
    },
    
    _onChangeUsers : function(e){


        var self = this;
        var users = $('#number_of_users').val();
        if (max_users !== 0 && users == max_users+1){
            alert("You cannot add more users.\nMaximum number of user reached!");
            $('#number_of_users').val(max_users);
            return;
        }
        // orm.call({
        //     model: 'saas.odoo.version',
        //     method: 'get_default_saas_values',
        //     args: [],
        // })
        this.orm.call('saas.odoo.version','get_default_saas_values',[])
        .then(function(data){
            var user_cost = data['user_cost'];
            if(max_users ==0){
                max_users = data['max_users'];
                if (users == max_users+1){
                    alert("You cannot add more users.\nMaximum number of user reached!");
                    $('#number_of_users').val(max_users);
                    return;
                }
            }   

            if (data['is_free_users']){
                users_price = (users - data['free_users']) * user_cost;
                if (users_price < 0){
                    users_price = 0;
                }
            }else{
                users_price = users * user_cost;
            }
            users_price = users_price * number
            $('#user_price_span').text(user_cost.toString());
            $('#total_users_value_span').text(users_price.toString()+' ');

            final_cost_value_span = users_price + total_app_value_span;
            self._check_discount();
            $('#discount_value_span').text(discount_value_span.toString()+' ');
            $('#final_cost_value_span').text(final_cost_value_span.toString()+' ');
            $('#pay_now_value_span').text(final_cost_value_span.toString()+' ');
        });            
    },

    _onClickBuyNow : function(ev){
        var self = this;
        var billing_type = $('#dropdownmenu3').text().trim();
        if (! billing_type){
            alert("Please select Billing Cycle");
            return;
        }
        if (apps.length == 0){
            alert("Please select Atleast one App..");
            return;
        }
        var recurring_interval = 0;
        if (billing_type == 'Monthly'){
            recurring_interval = 1;
        }
        else{
            recurring_interval = 12;
        }
        var users = $('#number_of_users');
        var version_code = $('#dropdownmenu2').attr('data-code');
        var version_name = $('#dropdownmenu2').text().trim();

        var number_of_users = parseInt(users.val());
        if (users.length && ! number_of_users){
            alert('Please Enter User to Continue');                
        }
        this.orm.call('saas.odoo.version','get_default_saas_values',[])
        .then(function(data){
            var user_cost = data['user_cost'];
            var total_cost = total_app_value_span;
            total_cost = self._check_if_discounted(total_cost);
            if (data['is_free_users']){
                user_cost = (number_of_users - data['free_users']) * user_cost * number;
                if (user_cost < 0){
                    user_cost = 0;
                }
                user_cost = self._check_if_discounted(user_cost);
            }
            else{
                user_cost = user_cost * number_of_users * number;
                user_cost = self._check_if_discounted(user_cost);
            }
            jsonrpc("/saas/add/plan", {
                'apps': apps,
                'saas_users': number_of_users,
                'version_code': version_code,
                'version_name': version_name,
                'total_cost': total_cost,
                'users_cost': user_cost,
                'recurring_interval' : recurring_interval,
            }).then(function(data){
                    if (data['status']){
                        location.href = '/shop/cart';
                        console.log(data)
                    }
                    else{
                        $('#error_message').show();
                    }
            });    
        });
    },
});
