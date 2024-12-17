// Copyright (c) 2024, Mohammed Nasser and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Payroll Rule", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Payroll Rule Route", "shift_type",function(frm,cdt, cdn)
{
var cur_grid = frm.get_field("table_baug").grid;
var cur_doc = locals[cdt][cdn];
var cur_row = cur_grid.get_row(cur_doc.name);
cur_row.toggle_view();
});
