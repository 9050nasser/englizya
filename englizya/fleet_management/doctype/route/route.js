// Copyright (c) 2024, Mohammed Nasser and contributors
// For license information, please see license.txt

frappe.ui.form.on("Route", {
	route_code(frm) {
        frm.set_value("title", frm.doc.route_code)
	},
});
