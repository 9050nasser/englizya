import frappe
import frappe.utils
@frappe.whitelist()
def on_submit(doc, method):
    if doc.custom_maintenance:
       maintenance = frappe.get_cached_doc('Maintenance', doc.custom_maintenance)
       maintenance.status = 'Completed'
       maintenance.save()
       pass

    # assets = frappe.new_doc('Asset')
    # assets.item_code = new_doc.name
    # assets.asset_category = 'cars'
    # assets.is_stock_item = 0
    # assets.flags.ignore_mandatory  = 1
    # assets.insert()
    pass