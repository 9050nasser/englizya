import frappe
from frappe import _
from datetime import datetime, date
import re

@frappe.whitelist()
def make_gl(posting_date, paid_to, paid_amount, against, voucher_type, voucher_no, party_type=None, party=None, cost_center=None):
    gl = frappe.new_doc("GL Entry")
    gl.posting_date = posting_date
    gl.account = paid_to
    if cost_center:
        gl.cost_center = cost_center
    if party:
        gl.party_type = party_type
        gl.party = party
    gl.credit = paid_amount
    gl.against = against
    gl.voucher_type = voucher_type
    gl.voucher_no = voucher_no
    gl.insert(ignore_permissions=True)
    gl.submit()
    gl = frappe.new_doc("GL Entry")
    gl.posting_date = posting_date
    gl.account = against
    if cost_center:
        gl.cost_center = cost_center
    if party:
        gl.party_type = party_type
        gl.party = party
    gl.debit = paid_amount
    gl.against = paid_to
    gl.voucher_type = voucher_type
    gl.voucher_no = voucher_no
    gl.insert(ignore_permissions=True)
    gl.submit()


@frappe.whitelist()
def generate_ticket_books(batch_code, total_books, category, item, serial, warehouse, company, tickets_per_book=200):
    start_serial = 1  # Starting serial number for the first book
    
    for i in range(int(total_books)):
        # Calculate serial range for this book
        start_serial_no = start_serial
        end_serial_no = start_serial + tickets_per_book - 1
        serial_no = serial[i]

        # Create a Ticket Book DocType entry
        try:
            book_doc = frappe.get_doc({
                "doctype": "Ticket Book",
                "name": f"{batch_code}-{i+1}",
                "book_code": i+1,  # Book identifier
                "batch_code": batch_code,
                "start_serial_no": start_serial_no,
                "end_serial_no": end_serial_no,
                "category": category,
                "item": item,
                "serial_no": serial_no,
                "warehouse": warehouse,
                "company": company
            })
            book_doc.insert()
        except Exception as e:
            frappe.log_error(f"Error inserting book {i+1} for batch {batch_code}: {str(e)}")

        # Update start serial number for the next book
        start_serial += tickets_per_book

        # Commit the transaction after every 1000 inserts to prevent memory issues
        if i % 1000 == 0:
            frappe.db.commit()

    # Commit the last set of books
    frappe.db.commit()

def generate_tickets(doc, method):
    for item in doc.items:
        try:
            bundles = frappe.get_doc("Serial and Batch Bundle", item.serial_and_batch_bundle)
            serial_numbers = tuple(bundle.serial_no for bundle in bundles.entries)
            
            batch_category = frappe.db.get_value("Batch", bundles.entries[0].batch_no, "custom_category")
            frappe.enqueue(
                generate_ticket_books,
                batch_code=bundles.entries[0].batch_no,
                total_books=item.qty,
                category=batch_category,
                item=item.item_code,
                serial= serial_numbers,
                warehouse=item.warehouse,
                company=doc.company,
                timeout=3600  # Adjust timeout if needed for large batches
            )
        except Exception as e:
            frappe.log_error(f"Error generating tickets for item {item.name}: {str(e)}")

def extract_numbers(input_string):
    for char in input_string:
        if char.isdigit():
            return int(input_string[input_string.index(char):])

def add_serials(doc, method):
    for entry in doc.entries:
        entry.custom_to_ticket = int(extract_numbers(entry.serial_no)) * 200
        entry.custom_from_ticket = (int(extract_numbers(entry.serial_no)) * 200) - 200 + 1

@frappe.whitelist()
def get_ticket_details(batch, start_serial=0):
    serial = int(start_serial)
    
    # Filters for start_serial and end_serial
    filters = {
        "batch_code": batch,
        
    }
    if serial in list(range(1, 999801, 200)):
        filters.update({
            "start_serial_no": ["=", serial],
            "end_serial_no": [">=", serial]
        })
    else:
        filters.update({
            "returned_ticket": ["=", serial]
        })
    
    
    # Fetch the ticket book data
    books = frappe.db.get_all("Ticket Book", filters=filters, fields=["*"])
    
    # Return the first matching book, or None if no match is found
    if books:
        return books[0]
    else:
        return None

def get_date(_date) -> str:
    if type(_date) == datetime:
        _date = _date.strftime("%Y-%m-%d %H:%M:%S")
    if type(_date) == date:
        _date = _date.strftime("%Y-%m-%d %H:%M:%S".split(" ")[0])
    return _date
@frappe.whitelist()
def appliy_salary(doc, method=None):
    emp = frappe.get_cached_doc('Employee', doc.employee)
    if emp.custom_roule_attendance:
        attendance_rule = frappe.get_cached_doc('Attendance Rule', emp.custom_roule_attendance)
        shift_type = frappe.get_cached_doc('Shift Type', doc.shift)

        # late_entry_grace_period = shift_type.late_entry_grace_period
        start_time = shift_type.start_time
        end_time = shift_type.end_time
        in_time = doc.in_time
        out_time = doc.out_time
        start_shift = datetime.strptime(f"{str(start_time)}", "%H:%M:%S")
        end_shift = datetime.strptime(f"{str(end_time)}", "%H:%M:%S")
        duration = (end_shift - start_shift).total_seconds() / 60 / 60
        max_allocation_over_time = (attendance_rule.max_allocation_over_time * 60) or 0 
        # Late Entry
        if doc.late_entry:
            time1_dt = datetime.strptime(f"{doc.attendance_date} {str(start_time)}", "%Y-%m-%d %H:%M:%S")
            time2_dt = datetime.strptime(str(in_time), "%Y-%m-%d %H:%M:%S")

            # Calculate the difference in minutes
            difference = (time2_dt - time1_dt).total_seconds() / 60
            # frappe.throw(f'{difference}')
            res = []
            data_dict = attendance_rule.as_dict()
            for row in data_dict.get('table_klrp'):
                if row['from'] < difference <= row['to'] :
                    res.append(row)
            data = frappe.db.sql(f"SELECT base FROM `tabSalary Structure Assignment` where employee = '{doc.employee}'  and docstatus = 1 order by name DESC ",as_dict = 1)
            
            if not res:
                res.append(data_dict.get('table_klrp')[-1])
            if data:
                amount = (((data[0]['base'] / 30)  / duration) / 60) * (difference * res[0].get('fraction', 1))
            if res:
                ads= frappe.new_doc('Additional Salary')
                ads.employee = doc.employee
                ads.salary_component = attendance_rule.late_salary_component
                ads.payroll_date = doc.attendance_date
                ads.ref_doctype = 'Attendance'
                ads.ref_docname = doc.name
                ads.amount =  amount
                ads.insert()
            pass
        if in_time or out_time:
            custom_min_overtime = frappe.db.sql(
                """
                SELECT SUM(custom_min_overtime)  as min_overtime
                FROM `tabAdditional Salary`
                WHERE salary_component = %s
                AND employee = %s
                AND MONTH(payroll_date) = MONTH(%s)
                AND YEAR(payroll_date) = YEAR(%s)
                """,
                (attendance_rule.late_salary_component, doc.employee, doc.attendance_date, doc.attendance_date)
            , as_dict = 1)
            if custom_min_overtime:
                minutes = custom_min_overtime[0]['min_overtime']
                out_time = datetime.strptime(f"{str(doc.out_time)}", "%Y-%m-%d %H:%M:%S")
                if minutes < max_allocation_over_time:
                    diff = max_allocation_over_time - minutes
                    end_shift_ =  datetime.strptime(f"{doc.attendance_date} {str(shift_type.end_time)}", "%Y-%m-%d %H:%M:%S")
                    overtime_min = ((out_time - end_shift_).total_seconds() / 60)
                    if overtime_min > float(shift_type.custom_gross_period_of_over_time):
                        if overtime_min <= diff:
                            from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday
                            fraction = attendance_rule.weakly_fraction_on_holiday if is_holiday(doc.attendance_date) else attendance_rule.holiday_fraction
                            data = frappe.db.sql(f"SELECT base FROM `tabSalary Structure Assignment` where employee = '{doc.employee}'  and docstatus = 1 order by name DESC ",as_dict = 1)
                            if data:
                                amount = (((data[0]['base'] / 30)  / duration) / 60) * (overtime_min * fraction)
                                ads= frappe.new_doc('Overtime Request')
                                ads.employee = doc.employee
                                ads.shift = doc.shift
                                ads.salary_component = attendance_rule.salary_component
                                ads.date = doc.attendance_date
                                ads.amount =  amount
                                ads.minutes =  overtime_min
                                ads.insert()



    pass
