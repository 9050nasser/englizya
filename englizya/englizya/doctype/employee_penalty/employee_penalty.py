# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime # from python std library
from frappe.utils import add_to_date

class EmployeePenalty(Document):
	def validate(self):
		self.penalty_number()
		self.calculate_installments()

	def penalty_number(self):
		all_penalties = frappe.db.get_all("Employee Penalty", filters={"docstatus": 1, "employee": self.employee})
		count = len(all_penalties) or 0
		self.penalty_no = count + 1
	@frappe.whitelist()
	def update_payment_schedule(self):
		# frappe.throw(f"{self.new_penalty_amount}")
		self.old_amount = self.penalty_amount
		self.penalty_amount = self.new_penalty_amount
		self.table_dahi = [row for row in self.table_dahi if row.is_accrued]
		self.calculate_update_payment_schedule()
		pass
	def calculate_update_payment_schedule(self):
		if self.is_a_term_penalty:
			if self.repayment_method == "Repay Fixed Amount per Period":
				fixed_amount = self.penalty_amount / self.monthly_repayment_amount
				# self.table_dahi = []
				for installment in range(1, int(fixed_amount + 1)):
					self.append("table_dahi", {
						"payment_date": add_to_date(self.payment_start_date, months=installment - 1),
						"principal_amount": self.monthly_repayment_amount,
						"balance_amount": self.penalty_amount - (installment * self.monthly_repayment_amount)
					})
			elif self.repayment_method == "Repay Over Number of Periods":
				duration = self.penalty_amount / ( self.repayment_period_in_months - len(self.table_dahi))
				# self.table_dahi = []
				range_cnt  = int(self.repayment_period_in_months - len(self.table_dahi) + 1)
				for installment in range(1, range_cnt):
					self.append("table_dahi", {
						"payment_date": add_to_date(self.payment_start_date, months=installment + len(self.table_dahi) - 1),
						"principal_amount": duration,
						"balance_amount": self.penalty_amount - (installment * duration)
					})
	def calculate_installments(self):
		if self.is_a_term_penalty:
			if self.repayment_method == "Repay Fixed Amount per Period":
				fixed_amount = self.penalty_amount / self.monthly_repayment_amount
				self.table_dahi = []
				for installment in range(1, int(fixed_amount + 1)):
					self.append("table_dahi", {
						"payment_date": add_to_date(self.payment_start_date, months=installment - 1),
						"principal_amount": self.monthly_repayment_amount,
						"balance_amount": self.penalty_amount - (installment * self.monthly_repayment_amount)
					})
			elif self.repayment_method == "Repay Over Number of Periods":
				duration = self.penalty_amount / self.repayment_period_in_months
				self.table_dahi = []
				for installment in range(1, int(self.repayment_period_in_months + 1)):
					self.append("table_dahi", {
						"payment_date": add_to_date(self.payment_start_date, months=installment - 1),
						"principal_amount": duration,
						"balance_amount": self.penalty_amount - (installment * duration)
					})

		
