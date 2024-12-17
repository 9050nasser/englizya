// Copyright (c) 2024, Mohammed Nasser and contributors
// For license information, please see license.txt

frappe.query_reports["Sahre Amount Payment Due"] = {
	"filters": [
		{
			"label":"License Plate No",
			"fieldname":"license_plate_no",
			"fieldtype":"Link",
			"options":"Vehicle",
		},
		{
			"label":"Customer",
			"fieldname":"customer",
			"fieldtype":"Link",
			"options":"Customer",
		}
	]
};
