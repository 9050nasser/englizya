# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff
def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns():
	return[
		{"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 200},
        {"label": _("Total Revenue"), "fieldname": "total_revenue", "fieldtype": "Float", "width": 200},
        {"label": _("Total Revenue Average"), "fieldname": "total_revenue_average", "fieldtype": "Float", "width": 200},
        {"label": _("Days Number"), "fieldname": "days_no", "fieldtype": "Float", "width": 200},
		{"label": _("Total Deduction"), "fieldname": "total_deduction", "fieldtype": "Float", "width": 200},
	]

def get_data(filters):
	result = []
	sql=f"""
		SELECT
			DATE_FORMAT(mn.date, '%Y-%m') AS month,
			SUM(mn.total_revenue) AS total_revenue,
			(SUM(mn.total_revenue) / COUNT(DISTINCT mn.date)) AS total_revenue_average,
			COUNT(DISTINCT mn.date) as days_no,
			1 as indent
		FROM
			`tabManifest` mn
		WHERE
			 mn.date BETWEEN '{filters.from_date}' AND '{filters.to_date}'
			 AND mn.status = '{filters.status}'
			 AND mn.driver = '{filters.driver}'
		GROUP BY
			DATE_FORMAT(mn.date, '%Y-%m')
		ORDER BY
			month;
	"""
	result.extend(frappe.db.sql(sql, as_dict=True))
	penalty_names = frappe.db.get_list("Employee Penalty", [["employee", "=", filters.driver], ["docstatus", "=", 1], ["penalty_date", "between", [filters.from_date, filters.to_date]]])
	total_deductions = 0
	for penalty in penalty_names:
		doc = frappe.get_doc("Employee Penalty", penalty.name)
		if doc.repayment_method == "Repay Over Number of Periods":
			for row in doc.table_dahi:
				if date_diff(row.payment_date, filters.from_date) >= 0 and date_diff(filters.to_date, row.payment_date) >= 0 and not row.is_accrued:
					total_deductions += row.principal_amount
		else:
			total_deductions += doc.penalty_amount
	result[0].total_deduction = total_deductions
	return result