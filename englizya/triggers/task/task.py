import frappe
import frappe.utils
@frappe.whitelist()
def validate(doc, method):
    if doc.custom_scheduled_maintenance and not doc.is_new() and doc.status == 'Completed':
        scheduled_maintenance = frappe.get_doc('Scheduled Maintenance', doc.custom_scheduled_maintenance)
        scheduled_maintenance.executed_times +=1
        scheduled_maintenance.maintenance_date  = scheduled_maintenance.next_maintenance_date
        scheduled_maintenance.next_maintenance_date = frappe.utils.add_days(scheduled_maintenance.next_maintenance_date, days= scheduled_maintenance.maintenance_cycle_period)
        scheduled_maintenance.save()

    # assets = frappe.new_doc('Asset')
    # assets.item_code = new_doc.name
    # assets.asset_category = 'cars'
    # assets.is_stock_item = 0
    # assets.flags.ignore_mandatory  = 1
    # assets.insert()
    pass