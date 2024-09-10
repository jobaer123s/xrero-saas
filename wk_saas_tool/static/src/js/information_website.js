odoo.define('saas_tool.information_website.', function(require) {
    "use strict";
    var core = require('web.core');
	var count = 0;
    var rpc = require('web.rpc');	
    var remaining_days = 0;
    var clear;
	// $(document).ready(function(){
		function check_instance_life() {
            var client_data = $('#trial_info');
            var self = this;
            var data = {
                'trial.is_trial_enabled': client_data.data('is_trial_enabled'),
                'trial.purchase_link': client_data.data('purchase_link'),
                'trial.trial_period': client_data.data('trial_period'),
            };
                if (data['trial.is_trial_enabled'] == 'True'){
                var content ='<div class="wk-destroy-info hidden-xs" id="wk-destroy-info" style="display:flex; width:45%;">';
                var expiry_text = null;
                if (Number(data['trial.trial_period']) == 0){
                    expiry_text = '<div class="row m-0 p-0" style="padding-top: 2% !important; padding-left: 2% !important;padding-bottom: 2%; width: 76%;"><div><span class="trial_expired_span" id="trial_expired_span" >Trial Expired</span><span class="wk-destroy-time"></span></div>'
                }
                else{
                    expiry_text = '<div class="row m-0 p-0" style="padding-top: 2% !important; padding-left: 2% !important;    padding-bottom: 2%; width: 76%;"><div><span class="trial_expired_span" id="trial_expired_span" >Your Trial Will Expire In </span><span class="wk-destroy-time"></span></div>'
                }
                var common_text = '<div style="width: 95% !important;"><p class="trial_expired_span">Satisfied With Odoo SaaS? Sign Up for your Unique Instance.</p></div></div>';
                var time_content = '<div class="justify-content-center flex-column d-flex"><a id ="store_link" target="_blank" class="btn btn-light btn-sm" style=" font-size:14px;" href='    +data['trial.purchase_link']+'>Purchase Now</a></div></div>';
                content = content + expiry_text +common_text +time_content;
                $('#footer').append(content);
				remaining_days = data['trial.trial_period'];
                get_secondsToHms(data);
				clear = setInterval(
						function() { get_secondsToHms(data); },
                        8.64*(10**7)
						
				);
                }
        }
		function get_secondsToHms(data) {
            var days = Number(remaining_days) - count;
            if(days > 0) {
                var days = Number(remaining_days) - count;
                var result = (days)
                console.log(result)
                if (result == 1){
                    result = result + ' Day '
                }else{
                    result = result + ' Days '
                }
                $('span.wk-destroy-time').text(result);
                count++;
            }else{
                clearInterval(clear);
                $('span#trial_expired_span').text('Trial Expired ');
                $('i.fa-clock-o').hide();   
                $('span.wk-destroy-time').hide();
            }
		}
		check_instance_life();
		});

// });
