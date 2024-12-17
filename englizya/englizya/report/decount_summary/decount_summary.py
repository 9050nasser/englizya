# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe import _
Filters = frappe._dict

def execute(filters: Filters = None) -> tuple:
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns() -> list[dict]:
    return [
        {"label": _("Route"), "fieldname": "route", "fieldtype": "Data", "width": 200},
        {"label": _("Shift"), "fieldname": "shift", "fieldtype": "Link", "options": "Shift Type", "width": 200},
        {"label": _("Driver"), "fieldname": "driver", "fieldtype": "Link", "options": "Employee", "width": 200},
        {"label": _("Car"), "fieldname": "car", "fieldtype": "Link", "options": "Vehicle", "width": 200},
        {"label": _("Manifest Date"), "fieldname": "date", "fieldtype": "Date", "width": 200},
        {"label": _("Manifest Name"), "fieldname": "manifest_name", "fieldtype": "Link", "options": "Manifest", "width": 200},
        {"label": _("Cash Income"), "fieldname": "cash", "fieldtype": "Float", "width": 200},
		{"label": _("Daily Salary"), "fieldname": "daily_salary", "fieldtype": "Float", "width": 200},
		{"label": _("Bonus"), "fieldname": "bonus", "fieldtype": "Float", "width": 200},
		{"label": _("Internal Diesel"), "fieldname": "internal_diesel", "fieldtype": "Float", "width": 200},
        {"label": _("External Diesel"), "fieldname": "external_diesel", "fieldtype": "Float", "width": 200},
		{"label": _("Invoice"), "fieldname": "invoice", "fieldtype": "Float", "width": 200},
        {"label": _("Bonus 5%"), "fieldname": "bonus_5", "fieldtype": "Float", "width": 200},
        {"label": _("Traffic"), "fieldname": "traffic", "fieldtype": "Float", "width": 200},
        {"label": _("Net Total"), "fieldname": "net_total", "fieldtype": "Float", "width": 200},
    ]


def get_data(filters: Filters) -> list[dict]:
    date = filters.get("date")
    garage = filters.get("garage")
    decount_type = filters.get("decount_type")
    status = filters.get("status")
    # Define specific routes you want to group by
    target_routes = frappe.db.get_all("Route", fields=["route_code"], pluck="route_code")
    
    # Initialize response list to accumulate data with separators
    response = []
    
    for route_code in target_routes:
        total = frappe.db.sql("""
            SELECT
                0 as shift,
                0 as driver,
                0 as car,
                0 as date,
                0 as name,
                sum(mn.total_revenue) as cash,
                sum(mn.daily_driver_amount) as daily_salary,
                sum(mn.elite_target_amount) as bonus,
                0 as internal_diesel,
                0 as external_diesel,
                0 as invoice,
                0 as bonus_5,
                0 as traffic,
                sum(mn.net_total) as net_total,
                "Total:" as route
            FROM `tabManifest` mn
            WHERE mn.status = %s AND mn.date = %s AND mn.garage = %s AND mn.manifest_type = %s AND mn.route = %s
        """, (status, date ,garage, decount_type, route_code), as_dict=True)[0]
        # Add a separator row for the route
        response.append({
            "cash": total.cash,
            "daily_salary": total.daily_salary,
            "bonus": total.bonus,
            "net_total": total.net_total,
            "route": f"Route {route_code}",
            "indent": 0  # This can be used to style the separator row if needed
        })
        
        # Fetch data for the specific route
        result = frappe.db.sql("""
            SELECT
                mn.shift as shift,
                mn.driver as driver,
                mn.vehicle as car,
                mn.date as date,
                mn.name as name,
                mn.total_revenue as cash,
                mn.daily_driver_amount as daily_salary,
                mn.elite_target_amount as bonus,
                0 as internal_diesel,
                0 as external_diesel,
                0 as invoice,
                0 as bonus_5,
                0 as traffic,
                mn.net_total as net_total,
                mn.route as route
            FROM `tabManifest` mn
            WHERE mn.status = %s AND mn.date = %s AND mn.garage = %s AND mn.manifest_type = %s AND mn.route = %s
        """, (status, date, garage, decount_type, route_code), as_dict=True)
        result.append(total)
        # Add each result row under the route section
        for row in result:
            response.append({
                "shift": row.shift,
                "driver": row.driver,
                "car": row.car,
                "date": row.date,
                "manifest_name": row.name,
                "cash": row.cash,
                "daily_salary": row.daily_salary,
                "bonus": row.bonus,
                "internal_diesel": row.internal_diesel,
                "external_diesel": row.external_diesel,
                "invoice": row.invoice,
                "bonus_5": row.bonus_5,
                "traffic": row.traffic,
                "net_total": row.net_total,
                "route": row.route,
                "indent": 1
            })
    
    return response