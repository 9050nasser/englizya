
frappe.ui.form.on("Employee", {
    custom_id_number: function (frm) {
    if(isNaN(frm.doc.custom_id_number) ||  frm.doc.custom_id_number.includes("."))
        frappe.throw(__("Id Number Not valid"))
    if(String(frm.doc.custom_id_number).length!=14)
        frappe.throw(__("Id Number Must be 14"))
	},

});
