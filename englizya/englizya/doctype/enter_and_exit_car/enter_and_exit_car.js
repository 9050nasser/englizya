// Copyright (c) 2024, Mohammed Nasser and contributors
// For license information, please see license.txt

frappe.ui.form.on("Enter And Exit Car", {
	refresh(frm) {

	},
    validate(frm){
        calculate_time(frm)
    },
    odometer_last(frm) {
        calculate_time(frm)
    }
});

function calculate_time(frm) {
    if (frm.doc.odometer_last && frm.doc.odometer_start) {

        frm.doc.km = frm.doc.odometer_last - frm.doc.odometer_start
    }
}
