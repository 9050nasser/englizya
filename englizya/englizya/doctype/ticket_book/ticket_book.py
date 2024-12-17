# Copyright (c) 2024, Mohammed Nasser and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TicketBook(Document):

	def generate_ticket_books(item_code, total_tickets, tickets_per_book, batch_code):
		total_books = total_tickets // tickets_per_book  # Calculate total number of books
		start_serial = 1  # Starting serial number for the first book
		
		for i in range(total_books):
			# Calculate serial range for this book
			start_serial_no = start_serial
			end_serial_no = start_serial + tickets_per_book - 1

			# Create a Ticket Book DocType entry
			book_doc = frappe.get_doc({
				"doctype": "Ticket Book",
				"book_code": i+1,  # Book identifier
				"batch_code": batch_code,
				"start_serial_no": start_serial_no,
				"end_serial_no": end_serial_no,
				"name": f"{batch_code}-{i+1}"
			})
			book_doc.insert()

			# Update start serial number for the next book
			start_serial += tickets_per_book

			# Commit the transaction after every 1000 inserts to prevent memory issues
			if i % 1000 == 0:
				frappe.db.commit()

		# Commit the last set of books
		frappe.db.commit()

# Example of generating books for 1 million tickets with 200 tickets per book
	# generate_ticket_books(
	# 	item_code="ticket",  # The item representing the ticket
	# 	total_tickets=1000000,  # Total number of tickets
	# 	tickets_per_book=200,  # Tickets per book
	# 	batch_code="BATCH001"  # Unique batch code for the million tickets
	# )


