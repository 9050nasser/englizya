# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EnterAndExitCar(Document):
	def validate(self):
		self.update_time_validate()

	def on_submit(self):
		self.update_time_submit()

	def update_time_validate(self):
		manifest = frappe.get_doc("Manifest", self.manifest)
		if self.exit and len(manifest.table_vsex) >= 1:
			manifest.table_vsex[0].exit = self.exit
			manifest.save(ignore_permissions=True)
		else:
			manifest.append("table_vsex", {
				"exit": self.exit
			})
			manifest.save(ignore_permissions=True)


	def update_time_submit(self):
		from datetime import datetime
		format_str = "%Y-%m-%d %H:%M:%S"
		if self.exit and self.enter:
			enter_time = datetime.strptime(self.enter, format_str)
			exit_time = datetime.strptime(self.exit, format_str)
			manifest = frappe.get_doc("Manifest", self.manifest)
			manifest.table_vsex[0].exit = self.exit
			manifest.table_vsex[0].enter = self.enter
			time_difference = enter_time - exit_time
			manifest.table_vsex[0].hours = time_difference.total_seconds() / 3600
			manifest.save(ignore_permissions=True)


