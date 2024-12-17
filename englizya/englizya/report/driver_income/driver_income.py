# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_columns(filters.group_by), get_data(filters)
	return columns, data


def get_columns(type) -> list[dict]:
	columns = [
        {"label": _("Driver"), "fieldname": "driver", "fieldtype": "Link", "options": "Employee", "width": 200},
        {"label": _("Driver Name"), "fieldname": "driver_name", "fieldtype": "Data", "width": 400},
        {"label": _("Total Revenue"), "fieldname": "total_revenue", "fieldtype": "Float", "width": 200},
        {"label": _("Mobile No."), "fieldname": "mobile_no", "fieldtype": "Data", "width": 200},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 200},
        {"label": _("Manifest Name"), "fieldname": "manifest_name", "fieldtype": "Link", "options": "Manifest", "width": 200},
    ]
	if type == "Consolidated":
		columns.append({"label": _("Average"), "fieldname": "average", "fieldtype": "Float", "width": 200})
	else:
		columns.append({"label": _("Route"), "fieldname": "route", "fieldtype": "Data", "width": 200})
	return columns

def get_conditions(filters):
	conditions = f"WHERE mn.date BETWEEN '{filters.from_date}' AND '{filters.to_date}' AND mn.status = '{filters.decount_status}' "
	if filters.decount_type:
		conditions += f" AND mn.manifest_type = '{filters.decount_type}' "
	if filters.driver:
		conditions += f" AND mn.driver = '{filters.driver}' "
	return conditions
def get_data(filters):
	data = []
	conditions = get_conditions(filters)
	if filters.group_by != "Consolidated":
		sql = """
			SELECT
				mn.driver as driver,
				mn.name as manifest_name,
				mn.total_revenue as total_revenue,
				mn.daily_driver_amount as daily_salary,
				mn.route as route,
				em.employee_name as driver_name,
				em.cell_number as mobile_no,
				em.status as status
			FROM `tabManifest` mn
			Join `tabEmployee` em
			ON mn.driver = em.name
		""" + conditions
	else :
		group_by = " GROUP BY mn.driver "
		sql = """
			SELECT
				mn.driver as driver,
				mn.name as manifest_name,
				SUM(mn.total_revenue) as total_revenue,
				SUM(mn.daily_driver_amount) as daily_salary,
				AVG(mn.total_revenue) AS average,
				em.employee_name as driver_name,
				em.cell_number as mobile_no,
				em.status as status
			FROM `tabManifest` mn
			Join `tabEmployee` em
			ON mn.driver = em.name
		""" + conditions + group_by
	data = frappe.db.sql(sql, as_dict = True)
	return data
