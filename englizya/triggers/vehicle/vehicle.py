import frappe
from  frappe import _
@frappe.whitelist()
def after_insert(doc,  method=None):
    for x in doc.custom_details:
        customer = frappe.get_doc("Customer", x.customer)
        exist_vechile = False
        for vehicle in customer.custom_details:
            if doc.name == vehicle.vehicle:
                exist_vechile = True
        if not exist_vechile:
            customer.append('custom_details',{
                "amount":x.amount,
                "percent":x.percent,
                "vehicle":doc.name,
            })
            customer.save()
            pass  
    pass
@frappe.whitelist()
def validate(doc, method=None):
    if doc.custom_is_customer_car:
        percent = 0
        for x in doc.custom_details:
            percent += x.percent
        if percent != 100:
            frappe.throw(_("Percentags Not equal 100"))

        if not  doc.custom_price_vehicle:
            return
        
        for x in doc.custom_details:
            x.amount = (doc.custom_price_vehicle * (x.percent / 100))
            pass
        if doc.is_new():
            return
        for x in doc.custom_details:
            customer = frappe.get_doc("Customer", x.customer)
            exist_vechile = False
            for vehicle in customer.custom_details:
                if doc.name == vehicle.vehicle:
                    exist_vechile = True
                    vehicle.amount = x.amount
                    vehicle.percent = x.percent
                    customer.save()
            if not exist_vechile:
                customer.append('custom_details',{
                    "amount":x.amount,
                    "percent":x.percent,
                    "vehicle":doc.name,
                })
                customer.save()
                pass  
        pass