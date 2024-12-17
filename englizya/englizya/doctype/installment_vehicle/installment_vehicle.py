# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date
from frappe import _

class InstallmentVehicle(Document):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.invoice_setting = frappe.get_cached_doc('Installment Vehicle Page')
        self.invoices = []
    def get_type_of_payment(self, customer):
        type_of_payment = None
        for pay in self.payments_details:
            if customer == pay.customer:
                if pay.type_of_payment == "Advanced":
                    type_of_payment = {
                                "amount": pay.advanced / pay.number_of_advanced,
                                "number": pay.number_of_advanced,
                                "number_of_months_period": pay.number_of_months_period,
                                "payment_type": pay.type_of_payment
                            }
                if pay.type_of_payment == "Installment":
                    type_of_payment = {
                               "amount": pay.payment_installment / pay.number_of_installments,
                                "number": pay.number_of_installments,
                                "payment_type": pay.type_of_payment
                            }
                if pay.type_of_payment == "Cash":
                    type_of_payment = {
                                "amount": pay.amount,
                                "number": 1,
                                "payment_type": pay.type_of_payment
                            }
                break
        return type_of_payment
    def get_payments(self, customer):
        payment_type = self.get_type_of_payment(customer)
        return payment_type or {}
        return {}
    def get_amount_gps(self,customer):
        amount_gps = 0
        for pay in self.details_gpsgarage:
            if customer == pay.customer:
                amount_gps = pay.amount_gps
        return amount_gps
    def get_amount_garage(self,customer):
        amount_garage = 0
        for pay in self.details_gpsgarage:
            if customer == pay.customer:
                amount_garage = pay.amount_garage
        return amount_garage
        return self.amount_garage
    def get_monthly_share_amount(self, customer):
        share_amount = 0
        for pay in self.payments_details:
            if customer == pay.customer:
                share_amount = pay.share_amount
        return share_amount
        return self.monthly_share_amount
    
    def create_payment_invoice(self, type, posting_date, amount, customer):
        sales_invoice = frappe.new_doc('Sales Invoice')
        sales_invoice.customer = customer
        sales_invoice.posting_date = posting_date
        sales_invoice.company = self.company
        sales_invoice.vehicle = self.vehicle
        sales_invoice.custom_installment_vehicle = self.name
        sales_invoice.due_date = frappe.utils.add_days(posting_date, days= 15)
        sales_invoice.set_posting_time = 1	
        sales_invoice.ignore_pricing_rule = 1	
        sales_invoice.remarks = type
        sales_invoice.append('items', {
            'item_code': type,
            'qty': 1,
            'rate': amount
        })
        self.invoices.append(sales_invoice)
        
    def get_item_invoice_based_payment(self, customer):
        payment_type = self.get_type_of_payment(customer)
        if payment_type.get('payment_type') == "Advanced":
            return self.invoice_setting.advanced
        elif payment_type.get('payment_type') == "Installment":
            return self.invoice_setting.installment
        elif payment_type.get('payment_type') == "Cash":
            return self.invoice_setting.cash
        pass
    def update_posting_date_invoice(self, posting_date, months = None, customer=None):
        if not months:
            months = self.get_payments(customer).get('number_of_months_period', 1)
        return add_to_date(posting_date, months=months, as_string=True)
        pass
    def apply_invoice_on_vehicle(self):
        for pay in self.payments_details:
            posting_date = self.next_subscription
            for x in range(self.get_payments(pay.customer).get('number', 0)):
                self.create_payment_invoice(self.get_item_invoice_based_payment(pay.customer), posting_date, self.get_payments(pay.customer).get('amount'), pay.customer)
                posting_date = self.update_posting_date_invoice(posting_date, customer = pay.customer)
    def apply_gps_invoice(self):
        posting_date = self.next_subscription
        for pay in self.details_gpsgarage:
            self.create_payment_invoice(self.invoice_setting.gps, posting_date, self.get_amount_gps(pay.customer), pay.customer)
    def apply_garage_invoice(self):
        posting_date = self.next_subscription
        for pay in self.details_gpsgarage:
            self.create_payment_invoice(self.invoice_setting.garage, posting_date, self.get_amount_garage(pay.customer), pay.customer)
    def apply_share_invoice(self):
        posting_date = self.next_subscription
        for pay in self.payments_details:
            if self.get_monthly_share_amount(pay.customer):
                for x in range(12):
                    self.create_payment_invoice(self.invoice_setting.share, posting_date, self.get_monthly_share_amount(pay.customer), pay.customer)
                    
                    posting_date = self.update_posting_date_invoice(posting_date, 1)
        pass
    def on_submit(self):
        self.apply_invoice_on_vehicle()
        if self.enable_gps:
            self.apply_gps_invoice()
        if self.enable_garage:
            self.apply_garage_invoice()
        self.apply_share_invoice()
        frappe.enqueue(long_submit_invoice, queue='short', invoices=self.invoices)
        self.next_subscription = frappe.utils.add_days(self.next_subscription, days= 30)
        pass
    def validate_percent(self):
            percent = 0
            for x in self.customer_installment:
                percent += x.percent
            percent2 = 0
            
            for x in self.payments_details:
                percent2 += x.percent
            percent3 = 0
            for x in self.details_gpsgarage:
                percent3 += x.percent
            if percent != 100 and percent2 != 100 and percent3 != 100:
                frappe.throw(_("Percentags Not equal 100"))
    def customer_has_installment_before(self):
        customer_list = [row.customer for row in self.customer_installment]
        customer_filter = ", ".join(f"'{customer}'" for customer in customer_list)
        # Updated query
        data = frappe.db.sql(f"""
            SELECT iv.name
            FROM `tabInstallment Vehicle` iv
            LEFT JOIN `tabCustomer Installment` ci ON iv.name = ci.parent
            WHERE ci.customer IN ({customer_filter})
            AND iv.vehicle = '{self.vehicle}'
            AND iv.name != '{self.name}'
        """)

        if data:
            frappe.throw(_("This Customer has Installment Before"))
    def validate(self):
        # Assuming self.customer_installment is a list of dictionaries or objects with a 'customer' field
        
        self.validate_percent()
        self.customer_has_installment_before()
        pass
    @frappe.whitelist()

    def set_amount_installment_in_payment_details(self, customer):
        data = frappe.db.sql(f"Select amount , customer_group, customer, percent FROM `tabC Group` where parent = '{self.vehicle}' and customer = '{customer}' ", as_dict= 1)
        if data:
            return data[0].get('amount')
        return 0
    @frappe.whitelist()
    def set_amount_installment(self):
        data = frappe.db.sql(f"Select amount , customer_group, customer, percent FROM `tabC Group` where parent = '{self.vehicle}' ", as_dict= 1)
        self.customer_installment = []
        for row in data:
            customer_installment = {
                "customer":row.get('customer'),
                "customer_group":row.get('customer_group'),
                "percent":row.get('percent'),
                "payment_installment": row.get('amount', 0) ,
                "advanced": row.get('amount', 0) ,
                "amount": row.get('amount', 0) ,
            }
            payments_details = {
                "customer":row.get('customer'),
                # "customer_group":row.get('customer_group'),
                "percent":row.get('percent'),
                # "payment_installment": row.get('amount', 0) ,
                # "advanced": row.get('amount', 0) ,
                # "amount": row.get('amount', 0) ,
            }
            self.append("customer_installment",customer_installment)
            self.append("payments_details",payments_details)
            self.append("details_gpsgarage",payments_details)
        #     if self.type_of_payment == "Advanced":
        #         self.advanced = row.get('amount', 0)
        #     elif self.type_of_payment == "Installment":
        #         self.payment_installment = row.get('amount', 0)            
        #     elif self.type_of_payment == "Cash":
        #         self.amount = row.get('amount', 0)
        # if data:
        #     if self.type_of_payment == "Advanced":
        #         self.advanced = data[0].get('amount', 0)
        #     elif self.type_of_payment == "Installment":
        #         self.payment_installment = data[0].get('amount', 0)            
        #     elif self.type_of_payment == "Cash":
        #         self.amount = data[0].get('amount', 0)
        pass
    @frappe.whitelist()
    def get_customer_group(self):
        data = frappe.db.sql(f"Select customer_group FROM `tabC Group` where parent = '{self.vehicle}' and customer= '{self.customer}' ", as_dict= 1)
        if data:
            self.customer_group = data[0].get('customer_group')
    pass

def long_submit_invoice(invoices):
    for invoice in invoices:
        invoice.insert()
        invoice.submit()
    pass
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_customer(doctype, txt, searchfield, start, page_len, filters):
    vehicle = filters.get("vehicle")

    if vehicle:
        # Use parameterized query to prevent SQL injection
        query = """
            SELECT customer 
            FROM `tabC Group` 
            WHERE parent = %s
        """
        return frappe.db.sql(query, (vehicle,))
    return []



