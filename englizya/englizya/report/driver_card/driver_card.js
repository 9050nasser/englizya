// Copyright (c) 2024, Mohammed Nasser and contributors
// For license information, please see license.txt

frappe.query_reports["Driver Card"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: new Date,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: new Date,
		},
		{
			fieldname: "driver",
			label: __("Driver"),
			fieldtype: "Link",
			options: "Employee",
			reqd: 1
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
		}
	]
};