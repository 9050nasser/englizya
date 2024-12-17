# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ScheduledMaintenance(Document):
	def generate_task(self):
		new_task = frappe.new_doc('Task')
		new_task.subject = f"""{self.maintenance_type} {self.vehicle} {self.maintenance_type} {self.item_code}"""
		new_task.custom_scheduled_maintenance = self.name
		new_task.exp_start_date= self.maintenance_date
		new_task.insert()
		# frappe.throw(f"{frappe.get_cached_value('Employee', self.name_of_the_maintenance_technician, 'user_id')}")
		args={
			"doctype" :"Task",
			"name" :new_task.name,
			"assign_to" :[frappe.get_cached_value('Employee', self.name_of_the_maintenance_technician, 'user_id')],
		}
		frappe.desk.form.assign_to.add(args)
		pass
	@frappe.whitelist()
	def validate(self):
		pass
	pass
