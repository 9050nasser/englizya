# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data


def get_data(filters):
    conditions = []
    invoice_setting = frappe.get_cached_doc('Installment Vehicle Page')
    if filters.get("customer"):
        conditions.append("si.customer = %(customer)s")
    if filters.get("license_plate_no"):
        conditions.append("si.vehicle = %(license_plate_no)s")

    conditions = " AND ".join(conditions) if conditions else "1=1"
    data =  frappe.db.sql(
        f"""
        SELECT 
            count(si.name) as number_of_due_monthes,iv.name as iv_veichle, si.remarks, si.vehicle as license_plate_no,iv.status, (iv.monthly_share_amount) as share_amount, iv.enable_gps as gps_subscription , iv.enable_garage, iv.vehicle_code,  si.customer, si.grand_total, SUM(si.grand_total) as total_due
        FROM `tabSales Invoice` si
        JOIN   `tabInstallment Vehicle`  iv on iv.name = si.custom_installment_vehicle
        WHERE {conditions}
        and si.status = 'Overdue'
        and si.remarks iN ('{invoice_setting.advanced}', '{invoice_setting.installment}', '{invoice_setting.cash}')
        GROUP BY si.vehicle, si.customer, si.custom_installment_vehicle
        """,
        filters,
        as_dict=True
    )
    for x in data :
        x['gps_subscription'] = _('Active') if x.get('gps_subscription') else _('Not Active')
        x['enable_garage'] = _('Active') if x.get('enable_garage') else _('Not Active')
    return data
    pass

def get_columns(filters):
    columns = [
        {
            "label":"License Plate No",
            "fieldname":"license_plate_no",
            "fieldtype":"Link",
            "options":"Vehicle",
            "width": 90
        },
        {
            "label":"iv_veichle",
            "fieldname":"iv_veichle",
            "fieldtype":"Link",
            "options":"Installment Vehicle",
            "width": 90
        },
        {
            "label":"Customer",
            "fieldname":"customer",
            "fieldtype":"Link",
            "options":"Customer",
            "width": 130
        },
        {
            "label":"Share Amount",
            "fieldname":"share_amount",
            "fieldtype":"Currency",
            "width": 130
        },
        {
            "label":"Installment",
            "fieldname":"remarks",
            "fieldtype":"Data",
            "width": 130
        },
        {
            "label":"Installment Amount",
            "fieldname":"grand_total",
            "fieldtype":"Currency",
            "width": 130
        },
        {
            "label":"Status",
            "fieldname":"status",
            "fieldtype":"Data",
            "width": 130
        },
        {
            "label":"GPS subscription",
            "fieldname":"gps_subscription",
            "fieldtype":"Data",
            "width": 130
        },
         {
            "label":"Garage subscription",
            "fieldname":"enable_garage",
            "fieldtype":"Data",
            "width": 130
        },
        {
            "label":"Vehicle Code",
            "fieldname":"vehicle_code",
            "fieldtype":"Data",
            "width": 130
        },
        {
            "label":"Number of Due Monthes",
            "fieldname":"number_of_due_monthes",
            "fieldtype":"Int",
            "options":"Customer",
            "width": 130
        },
        {
            "label":"Total Due",
            "fieldname":"total_due",
            "fieldtype":"Currency",
            "width": 130
        },
    ]

    return columns
