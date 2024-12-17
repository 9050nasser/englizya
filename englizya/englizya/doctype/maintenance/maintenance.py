# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Maintenance(Document):
	@frappe.whitelist()
	def create_stock_entry(self, warehouse):
		stock_entry = frappe.new_doc('Stock Entry')
		stock_entry.stock_entry_type = "Material Issue"
		stock_entry.company = self.company
		stock_entry.custom_maintenance = self.name
		for item in self.item_vehicle:

			stock_entry.append('items',{
				's_warehouse':warehouse,
				'item_code':item.spare_parts,
				'qty':item.qty,
				'stock_uom':item.unit,
			})
		stock_entry.insert()
		frappe.msgprint("تم انشاء حركة مخزنية")
	def after_insert(self):
		custom_warehouse = frappe.get_doc('Branch', self.location).custom_warehouse
		self.create_stock_entry(custom_warehouse)
		pass
	def validate(self):
		if self.is_new():
			self.status = "New"
		pass
	def on_submit(self):
		if self.status != "Completed":
			frappe.throw(f"يجب  الموافقة على الحركة المخزنية")
			# for x in self.table_qwhg:
			# 	x.start_date = x.next_due_date
			# 	x.next_due_date = frappe.utils.add_days(x.next_due_date, days= x.count)
			# self.executed +=1
		pass
		
	pass
