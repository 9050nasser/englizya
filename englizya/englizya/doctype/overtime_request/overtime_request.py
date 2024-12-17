# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OvertimeRequest(Document):
	def on_submit(self):
		if self.status == "Approved":
			ads = frappe.new_doc('Additional Salary')
			ads.employee = self.employee
			ads.salary_component = self.salary_component
			ads.payroll_date = self.date
			ads.amount =  self.amount
			ads.custom_min_overtime =  self.minutes
			ads.ref_doctype = 'Overtime Request'
			ads.ref_docname = self.name
			ads.insert()
			ads.submit()
		pass
	pass
