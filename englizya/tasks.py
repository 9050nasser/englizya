import frappe
@frappe.whitelist()
def update_maintaince():
    data = frappe.db.sql(f"""SELECT parent , assign_to
                                FROM `tabMaintenance Table`
                                WHERE next_due_date = CURDATE();
        """,as_dict = 1)
    if data:
        for x in data:
            args={
                    "doctype" :'Maintenance',
                    "name" :x['parent'],
                    "assign_to" :[x['assign_to']],
                }
            frappe.desk.form.assign_to.add(args)
    data = frappe.db.sql(f"""SELECT name, enable_gps, enable_garage, amount_gps, amount_garage, start_date
                                FROM `tabInstallment Vehicle`
                                WHERE next_subscription = CURDATE() and (enable_garage = 1 or  enable_gps = 1);
        """,as_dict = 1)
    frappe.db.commit()
    invoices = []
    for x in data:
        doc = frappe.get_doc('Installment Vehicle', x['name'])
        if x.get('enable_gps'):
            doc.apply_gps_invoice()
        if x.get('enable_garage'):
            doc.apply_garage_invoice()
        doc.next_subscription = frappe.utils.add_days(doc.next_subscription, days=30)
        invoices.extend(doc.invoices)
        doc.save()
    for x in invoices:
        x.save()
        x.submit()
    # pass