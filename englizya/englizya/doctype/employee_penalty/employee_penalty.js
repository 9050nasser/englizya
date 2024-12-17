// Copyright (c) 2024, Mohammed Nasser and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Penalty", {
	refresh(frm) {
        if(frm.doc.docstatus ==1){
            frm.add_custom_button(__("Update Penalty Amount"), function() {
                let d = new frappe.ui.Dialog({
                    title: 'Enter details',
                    fields: [
                        {
                            label: 'New Penalty Amount',
                            fieldname: 'new_penalty_amount',
                            fieldtype: 'Currency'
                        }
                    ],
                    size: 'small', // small, large, extra-large 
                    primary_action_label: 'Update',
                    primary_action(values) {
                        frm.doc.new_penalty_amount = values.new_penalty_amount
                        frappe.call({
                            method:'update_payment_schedule',
                            doc: frm.doc,
                            callback: function(r){
                                frm.save('Update')
                            }
                        })
                        d.hide();
                    }
                });
                
                d.show();
                
                
            });
        }
	},
});
