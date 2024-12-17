
frappe.ui.form.on("Customer", {
    refresh: function (frm) {
		frm.set_query("custom_vehicle", function() {
            return {
                filters: [
                    ["custom_customer", "=", frm.doc.name]
                ]
            };
        });
	},

});
