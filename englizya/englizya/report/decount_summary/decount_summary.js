// Copyright (c) 2024, Mohammed Nasser and contributors
// For license information, please see license.txt

frappe.query_reports["Decount Summary"] = {
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
			],
			reqd: 1,
			default: "Internal"
		},
		{
			fieldname: "status",
			label: __("Decount Status"),
			fieldtype: "Select",
			options: [
				"Pending",
				"Calculate",
				"First Review",
				"Complete The First Review",
				"Second Review",
				"Complete The Second Review"
			],
			reqd : 1,
			default: "Complete The Second Review"
		},
	]
};
