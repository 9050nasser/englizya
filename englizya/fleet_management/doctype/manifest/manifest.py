# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
import erpnext
from frappe.utils import comma_and, cstr, flt, fmt_money, formatdate, get_link_to_form, nowdate, today, now
class Manifest(Document):

	def validate(self):
		self.get_target_amount()
		# self.check_booked_before_or_not()
		self.update_ticket_book()
		self.assign_driver()
		self.make_stock_entry()

		

	def on_cancel(self):
		self.cancel_gl_entries()

	def on_submit(self):
		self.create_custom_gl_entry_for_doctype()

	def make_stock_entry(self):
		if self.status=="Pending":
			warehouse=frappe.db.get_value("Branch", self.garage, "custom_warehouse")
			stock_entry=frappe.get_doc({
				"doctype": "Stock Entry",
				"company": self.company,
				"stock_entry_type": "Material Issue",
				"posting_date": today(),
				"posting_time": now(),
				"items": [
					{
						"s_warehouse": warehouse,
						"item_code": row.item or "تذكررة",
						"qty": 1,
						"use_serial_batch_fields": 1,
						"batch_no": row.letter,
						"serial_no": row.serial_no,
						"vehicle": self.vehicle
					}
					for row in self.table_fozg
				]
			})
			stock_entry.insert()
			stock_entry.submit()
			self.stock_entry = stock_entry.name
			frappe.db.commit()

	def get_target_amount(self):
		route = frappe.get_doc("Payroll Rule", self.route)
		for row in route.table_baug:
			if row.shift_type == self.shift:
				self.daily_driver_amount = (row.daily_percentage * self.total_revenue / 100) if route.payroll_calculation == "Percentage" else row.daily_fixed_amount
				self.mouthly_driver_amount = (row.daily_percentage_end_of_month_amount * self.total_revenue / 100) if route.payroll_calculation == "Percentage" else row.fixed_end_of_month_amount
				if self.total_revenue > row.to_daily_revenue_target and self.sold_tickets_count > row.daily_ticket_sales_count:
					if self.sold_tickets_count >= (row.extra_ticket_sales_count + row.daily_ticket_sales_count) and self.total_revenue >= row.extra_ticket_target_amount:
						self.over_target_amount = (self.total_revenue - row.to_daily_revenue_target) * row.daily_extra_ticket_bonus__percentage / 100
						if (self.total_revenue - row.to_daily_revenue_target) >= row.elite_ticket_target_amount and (self.sold_tickets_count - row.daily_ticket_sales_count) >= row.elite_ticket_sales_count:
							self.elite_target_amount = row.daily_elite_ticket_bonus_amount
	def assign_driver(self):
		if self.status == "Pending":
			for row in self.table_fozg:
				book = frappe.get_doc("Ticket Book", row.ticket_book)
				book.driver = self.driver
				# book.manifest = self.name 
				book.save()
			frappe.db.commit()

	def update_ticket_book(self):
		if self.status =="Calculate":
			'''Update ticket book with ticket book status and update return ticket number'''
			for row in self.table_fozg:
				book = frappe.get_doc("Ticket Book", row.ticket_book)
				if row.ticket_return_no > getattr(row, 'from') and row.ticket_return_no <= int(row.to): 
					book.returned_ticket = row.ticket_return_no
					book.status = "Partly Sold"
					book.driver = self.driver
					book.manifest = self.name
					book.save()
					
				elif row.ticket_return_no == 0:
					book.status = "Sold"
					book.driver = self.driver
					book.manifest = self.name
					book.save()
				frappe.db.commit()

	def get_daily_salary(self):
		percentage = frappe.db.get_value("Driver", self.driver, "custom_driver_percentage_")
		if percentage and self.total_revenue:
			self.daily_salary = percentage * self.total_revenue / 100
		if self.total_revenue and self.total_expense:
			self.net_total = self.total_revenue - self.total_expense
		if self.fuel_qty and self.fuel_price__l:
			self.amount = self.fuel_qty * self.fuel_price__l

	def get_avg_fuel(self):
		self.معدل_استهلاك_البنزين = self.fuel_qty / (float(self.current_odometer_value - self.last_odometer_value)) *100

	def check_booked_before_or_not(self):
		for row in self.table_fozg:
			if row.exists_or_not == 0:
				book = frappe.get_doc("Ticket Book", row.ticket_book)
				if book.status_book == "Close":
					frappe.throw(f"Tickets Booked before")
				else:
					book.status_book = "Open"
					book.save()
				row.exists_or_not = 1
	@frappe.whitelist()
	def create_journal_entry(self):




		JE = frappe.new_doc('Journal Entry')
		vehicle = frappe.get_cached_doc('Vehicle', self.vehicle)
		expense_text = ''
		for row in self.details:
			expense_text += f'/ {row.expenses}'
		JE.voucher_type = 'Journal Entry'
		JE.posting_date = datetime.now()
		JE.append('accounts',{
			'account': self.garage_account,
			'debit_in_account_currency':self.total_revenue
		})
		JE.append('accounts',{
			'account': vehicle.custom_revenue_account,
			'credit_in_account_currency':self.total_revenue
		})
		
		JE.append('accounts',{
			'account': vehicle.custom_expenses_account,
			'debit_in_account_currency':self.total_expense,
			'user_remark': expense_text
		})
		JE.append('accounts',{
			'account': self.garage_account,
			'credit_in_account_currency': self.total_expense
		})
		JE.user_remark =  expense_text
		JE.insert()
		JE.submit()
		pass


	from frappe.utils import flt, nowdate

	def custom_make_gl_entry(self, account, debit=0, credit=0, party_type=None, party=None, against=None, voucher_type=None, voucher_no=None, cost_center=None, posting_date=None, company=None, remarks=None):
		# Initialize a new GL entry
		gl_entry = frappe.get_doc({
			"doctype": "GL Entry",
			"account": account,
			"debit": flt(debit),
			"credit": flt(credit),
			"party_type": party_type,
			"party": party,
			"against": against,
			"voucher_type": voucher_type,
			"voucher_no": voucher_no,
			"cost_center": cost_center,
			"posting_date": posting_date or nowdate(),
			"company": company,
			"remarks": remarks,
			"fiscal_year": frappe.defaults.get_global_default("fiscal_year")
		})

		# Insert and submit the entry to save it in the database
		gl_entry.insert()
		gl_entry.submit()
		frappe.db.commit()

	def create_custom_gl_entry_for_doctype(self):
		# Call custom GL entry function for debit and credit entries
		car = frappe.get_doc("Vehicle", self.vehicle)
		garage = frappe.get_doc("Branch", self.garage)
		company = frappe.get_doc("Company", self.company)

		# Income GL Entry
		self.custom_make_gl_entry(
			
			account= company.default_income_account,
			debit=0,
			credit=self.total_revenue,
			party_type="",
			party="",
			against=garage.custom_treasury,
			voucher_type=self.doctype,
			voucher_no=self.name,
			cost_center= car.custom_cost_center,
			posting_date=self.date,
			company = self.company
		)

		self.custom_make_gl_entry(
			account = garage.custom_treasury,
			debit=self.total_revenue,
			credit=0,
			against=car.custom_revenue_account,
			voucher_type=self.doctype,
			voucher_no=self.name,
			cost_center=car.custom_cost_center,
			posting_date=self.date,
			company = self.company
		)

		if self.details:
			#Expenses GL Entry
			for row in self.details:
				ex_type= frappe.get_doc("Expense Claim Type", row.expenses)
				for ex in ex_type.accounts:
					if self.company == ex.company:
						self.custom_make_gl_entry(
							account = garage.custom_treasury,
							debit=0,
							credit=row.value,
							against= ex.default_account,
							voucher_type=self.doctype,
							voucher_no=self.name,
							cost_center=car.custom_cost_center,
							posting_date=self.date,
							company = self.company,
							remarks= row.expenses or row.notes
						)
						self.custom_make_gl_entry(
							
							account= ex.default_account,
							debit=row.value,
							credit=0,
							party_type="",
							party="",
							against=garage.custom_treasury,
							voucher_type=self.doctype,
							voucher_no=self.name,
							cost_center= car.custom_cost_center,
							posting_date=self.date,
							company = self.company,
							remarks= row.expenses or row.notes
						)


	def create_stock_entry(self):
		stock_entry = frappe.get_doc({
			"doctype": "Stock Entry",

		})

	def cancel_gl_entries(self):
		gl_entries = frappe.get_all('GL Entry', filters={
        'voucher_type': self.doctype,
        'voucher_no': self.name
    })
    
    # Loop through the GL entries and cancel each one
		for entry in gl_entries:
			gl_entry = frappe.get_doc('GL Entry', entry.name)
			gl_entry.delete()
			frappe.db.commit()



