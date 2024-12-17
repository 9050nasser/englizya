# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class MaintenancePage(Document):
	@frappe.whitelist()
	def make_scheduled_maintenance(self):
		target_doc = frappe.new_doc('Scheduled Maintenance')
		target_doc.name_of_the_maintenance_technician = self.name_of_the_maintenance_technician
		target_doc.maintenance_type = self.maintenance_type
		target_doc.maintenance_date = self.maintenance_date
		target_doc.maintenance_calculation = self.maintenance_calculation
		target_doc.maintenance_cycle_period = self.maintenance_cycle_period
		target_doc.unit = self.unit
		target_doc.vehicle = self.vehicle
		target_doc.next_maintenance_date = self.next_maintenance_date
		target_doc.location = self.location
		target_doc.quantity_used = self.quantity_used
		target_doc.item_code = self.item_code
		target_doc.insert()
		target_doc.generate_task()
	@frappe.whitelist()
	def create_scheduled_maintenance(self):
		self.make_scheduled_maintenance()
		
		pass
	pass



