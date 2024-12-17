// Copyright (c) 2024, Mohammed Nasser and contributors
// For license information, please see license.txt
frappe.ui.form.on("Maintenance", {
    refresh: function(frm) {
        frm.set_query("spare_parts", "item_vehicle",function() {
            return {
                filters: [
                    ["custom_maintenance_type", "=", frm.doc.maintenance_type]
                ]
            };
        });
        frm.set_query("vehicle", function() {
            return {
                filters: [
                    ["custom_company", "=", frm.doc.company]
                ]
            };
        });
    }
});
frappe.ui.form.on("Maintenance", {
	refresh(frm) {
    
        
	},
    maintenance_type(frm){
        // frm.set_value('spare_parts', '')
    }
});

frappe.ui.form.on("Maintenance Table", {
	start_date(frm,cdt,cdn) {
        var z = locals[cdt][cdn];
        if(z.count)
            z.next_due_date =  frappe.datetime.add_days(z.start_date, z.count)
        frm.refresh_field('table_qwhg')
	},
    count(frm,cdt,cdn) {
        var z = locals[cdt][cdn];
        if(z.start_date)
            z.next_due_date =  frappe.datetime.add_days(z.start_date, z.count)
        z.assign_to =  frappe.session.user
        frm.refresh_field('table_qwhg')

	},
    next_due_date(frm,cdt,cdn) {
        console.log("heeeeeeeeeeeeey")
        var z = locals[cdt][cdn];
        
	},
    
});
