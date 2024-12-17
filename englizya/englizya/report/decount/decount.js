// Copyright (c) 2024, Mohammed Nasser and contributors
// For license information, please see license.txt

frappe.query_reports["Decount"] = {
	filters: [
		{
			fieldname: "date",
			label: __("Date"),
			fieldtype: "Date",
			reqd: 1,
			default: new Date,
		},
		{
			fieldname: "garage",
			label: __("Garage"),
			fieldtype: "Link",
			options: "Branch",
			reqd: 1,
		},
		{
			fieldname: "decount_type",
			label: __("Decount Type"),
			fieldtype: "Select",
			options: [
				"Internal",
				"External"
			]
		},
	]
};
