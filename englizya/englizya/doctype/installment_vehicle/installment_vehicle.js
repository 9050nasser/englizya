// Copyright (c) 2024, Mohammed Nasser and contributors
// For license information, please see license.txt

frappe.ui.form.on("Installment Vehicle", {
    refresh(frm){

        frm.set_query('vehicle', function() {
            if(frm.doc.company)
                return {
                    filters: { 'custom_company': frm.doc.company }
                };
        });
        
    },
    // customer(frm){
    //     if(frm.doc.customer)
    //         frappe.call({
    //             method:"get_customer_group",
    //             doc:frm.doc,
    //             callback:function(r){
    //                 frm.refresh_field('customer_group')
    //             }
    //     })
    // },
    vehicle(frm){
            frappe.call({
                method:"set_amount_installment",
                doc:frm.doc,
                callback:function(r){
                    frm.refresh_field('customer_installment')
                    frm.refresh_field('payments_details')
                    frm.refresh_field('details_gpsgarage')

                }
        })
    },
    amount_gps(frm){
        if(frm.doc.customer_installment)
        {
            frm.doc.customer_installment.forEach(element => {
                element.amount_gps = frm.doc.amount_gps* (element.percent / 100)
            });
            frm.doc.details_gpsgarage.forEach(element => {
                element.amount_gps = frm.doc.amount_gps* (element.percent / 100)
            });
        }
        frm.refresh_field('customer_installment')
        frm.refresh_field('details_gpsgarage')

},

amount_garage(frm){
    if(frm.doc.customer_installment)
    {
        frm.doc.customer_installment.forEach(element => {
            element.amount_garage = frm.doc.amount_garage* (element.percent / 100)
        });
        frm.doc.details_gpsgarage.forEach(element => {
            element.amount_garage = frm.doc.amount_garage* (element.percent / 100)
        });
    }
    frm.refresh_field('customer_installment')
    frm.refresh_field('details_gpsgarage')
},
	share_amount(frm) {
        if (frm.doc.share_amount)
            frm.set_value('monthly_share_amount', frm.doc.share_amount/ 12)
	},
    monthly_share_amount(frm) {
        if (frm.doc.monthly_share_amount)
            frm.set_value('share_amount', frm.doc.monthly_share_amount * 12)
        if(frm.doc.payments_details)
            frm.doc.payments_details.forEach(element => {
                element.share_amount = frm.doc.monthly_share_amount* (element.percent / 100)
            
        });
        frm.doc.customer_installment.forEach(element => {
            element.share_amount = frm.doc.monthly_share_amount* (element.percent / 100)
            
        });
        frm.refresh_field('payments_details')
        frm.refresh_field('customer_installment')

	},
    start_date(frm) {
        if (frm.doc.start_date)
            frm.set_value('next_subscription', frm.doc.start_date)
	},
});

frappe.ui.form.on("Payments Details", {
    type_of_payment(frm, cdt, cdn){
        var d = locals[cdt][cdn];
        if(d.type_of_payment)
            frappe.call({
                method:"set_amount_installment_in_payment_details",
                doc:frm.doc,
                args:{
                    customer:d.customer
                },
                callback:function(r){
                    if(d.type_of_payment== "Cash"){
                        d.payment_installment = 0 
                        d.advanced = 0 
                        d.amount = r.message 
                    }
                    if(d.type_of_payment== "Advanced"){
                        d.payment_installment = 0 
                        d.advanced = r.message  
                        d.amount = 0
                    }
                    if(d.type_of_payment== "Installment"){
                        d.payment_installment = r.message 
                        d.advanced = 0 
                        d.amount = 0
                    }
                    frm.refresh_field('customer_installment')
                    frm.refresh_field('payments_details')
                    frm.refresh_field('details_gpsgarage')

                }
            })
        
    },

    
});
