# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	conditions = get_conditions(filters)
	columns, data = get_columns(filters.group_by), get_data(conditions, filters.group_by)
	return columns, data


def get_conditions(filters):
	conditions = f"WHERE mn.date BETWEEN '{filters.from_date}' AND '{filters.to_date}' AND mn.status = '{filters.status}' "
	if filters.decount_type:
		conditions += f" AND mn.manifest_type = '{filters.decount_type}' "
	if filters.route:
		conditions += f" AND mn.route = '{filters.route}' "
	if filters.garage:
		conditions += f" AND mn.garage = '{filters.garage}' "
	if filters.group_by == "Consolidated":
		conditions += " GROUP BY mn.vehicle "
	return conditions

def get_columns(type):
	columns = [
        {"label": _("Car"), "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 200},
        {"label": _("Total Revenue"), "fieldname": "total_revenue", "fieldtype": "Float", "width": 200},
        {"label": _("Net Total"), "fieldname": "net_total", "fieldtype": "Float", "width": 200},
    ]
	if type == "Consolidated":
		columns.append({"label": _("Total Revenue Average"), "fieldname": "total_revenue_average", "fieldtype": "Float", "width": 200})
		columns.append({"label": _("Net Total Average"), "fieldname": "net_total_average", "fieldtype": "Float", "width": 200})
	else:
		columns.append({"label": _("Route"), "fieldname": "route", "fieldtype": "Data", "width": 200})
		columns.append({"label": _("Manifest Name"), "fieldname": "manifest_name", "fieldtype": "Link", "options": "Manifest", "width": 200})
	return columns


def get_data(conditions, type):
	if type == "Consolidated":
		sql = f"""
			SELECT
				SUM(mn.total_revenue) as total_revenue,
				mn.vehicle as vehicle,
				SUM(mn.net_total) as net_total,
				AVG(mn.total_revenue) as total_revenue_average,
				AVG(mn.net_total) as net_total_average
			FROM `tabManifest` mn
			{conditions}
		"""
	else:
		sql = f"""
			SELECT
				mn.total_revenue as total_revenue,
				mn.vehicle as vehicle,
				mn.net_total as net_total,
				mn.route as route,
				mn.name as manifest_name
			FROM `tabManifest` mn
			{conditions}
		"""
	# frappe.throw(sql)
	return frappe.db.sql(sql, as_dict = True)
