// Copyright (c) 2024, Mohammed Nasser and contributors
// For license information, please see license.txt
const requiredFields = {
    name_of_the_maintenance_technician: "Name of the Maintenance Technician",
    maintenance_type: "Maintenance Type",
    maintenance_date: "Maintenance Date",
    maintenance_calculation: "Maintenance Calculation",
    // maintenance_cycle_period: "Maintenance Cycle Period",
    unit: "Unit",
    vehicle: "Vehicle",
    next_maintenance_date: "Next Maintenance Date",
    location: "Location",
    quantity_used: "Quantity Used",
    item_code: "Item Code"
};
frappe.ui.form.on("Maintenance Page", {
	refresh(frm) {
        frm.disable_save()
        frm.add_custom_button(__('Add Maintenance Schedule'), function () {

            Object.entries(requiredFields).forEach(([field, label]) => {
                if (!frm.doc[field]) {
                   frappe.throw(__(`The field '${label}' is required and cannot be empty.`))
                }
            });
            frappe.call({
                method:'create_scheduled_maintenance',
                doc: frm.doc
            })
            
        });
	},
    maintenance_cycle_period(frm){
        if(frm.doc.maintenance_cycle_period){
            frm.set_value('next_maintenance_date', frappe.datetime.add_days(frappe.datetime.nowdate(), frm.doc.maintenance_cycle_period))
        }
    }
});
