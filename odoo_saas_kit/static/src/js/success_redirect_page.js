/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
// import rpc from "@web/legacy/js/core/rpc";
// import ajax from "@web/legacy/js/core/ajax";


publicWidget.registry.SaasAccountRedirect = publicWidget.Widget.extend({
    selector: '.redirect_page_div',
    events: {

        'click .go_to_account': '_onClickGoToAcc',
    },

    init() {
        this._super(...arguments);
        // this.rpc = this.bindService("rpc");
        this.orm = this.bindService("orm");
    },
    
    _onClickGoToAcc: function(ev){
        var contract_id = $(ev.currentTarget).val();
        // rpc.query({model: 'saas.contract', method: 'redirect_invitation_url', args: [contract_id],})
        this.orm.call("saas.contract", "redirect_invitation_url", [contract_id])
        .then(function(url){
            location.href=url;
        });
    },
    
});
