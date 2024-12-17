import frappe
from datetime import datetime


def calculate_salary(doc, method):
    # Fetch manifests for the driver within the specified date range
    manifests = frappe.db.get_all(
        "Manifest", 
        filters={"docstatus": 1, "driver": doc.employee, "date": ["Between", [doc.start_date, doc.end_date]]},
        fields=["*"]
    )

    assignments = frappe.get_all("Salary Structure Assignment", 
                            filters={"employee": doc.employee, "from_date": ["<=", doc.start_date], "docstatus": 1},
                            fields=["*"])

    if assignments:
        daily_assignments = []
        
        for assignment in assignments:
            structure = frappe.get_doc("Salary Structure", assignment.salary_structure)
            if structure.payroll_frequency == "Daily":
                daily_assignments.append(structure.name)
            elif structure.payroll_frequency == "Monthly":
                daily_assignments.append(structure.name)
        
        if daily_assignments:
            print(daily_assignments[0])
            doc.salary_structure = daily_assignments[0]
        else:
            print("No daily assignments found")

    if doc.payroll_frequency == "Daily":
        # Initialize totals for the salary components
        total_daily_driver_amount = 0
        total_over_target_amount = 0
        total_elite_target_amount = 0
        data = frappe.db.sql(f"""
                SELECT count(name)  as num_cnt, maintain_same_bus_bonus,route, shift from `tabManifest` where driver = '{doc.employee}' and date between '{doc.start_date}' and '{doc.end_date}' and docstatus = 1 group by vehicle, maintain_same_bus_bonus
            """, as_dict = 1)
        payroll_pay =  frappe.get_cached_doc("Payroll Rule", data[-1].get('route'))
        # Sum the amounts from each manifest
        for manifest in manifests:
            total_daily_driver_amount += manifest.daily_driver_amount or 0
            total_over_target_amount += manifest.over_target_amount or 0
            total_elite_target_amount += manifest.elite_target_amount or 0
        # doc.salary_structure = "هيكل قبض يومى"
        # Append each salary component with its calculated total
        
        if total_daily_driver_amount > 0:
            doc.append("earnings", {
                "salary_component": payroll_pay.table_baug[0].get('daily_salary_component'),
                "amount": total_daily_driver_amount
            })
        
        if total_over_target_amount > 0:
            doc.append("earnings", {
                "salary_component": payroll_pay.table_baug[0].get('extra_salary_component'),
                "amount": total_over_target_amount
            })
        
        if total_elite_target_amount > 0:
            doc.append("earnings", {
                "salary_component": payroll_pay.table_baug[0].get('elite_salary_component'),
                "amount": total_elite_target_amount
            })
    elif doc.payroll_frequency == "Monthly":
        data = frappe.db.sql(f"""
                SELECT count(name)  as num_cnt, maintain_same_bus_bonus,route, shift from `tabManifest` where driver = '{doc.employee}' and date between '{doc.start_date}' and '{doc.end_date}' and docstatus = 1 group by vehicle, maintain_same_bus_bonus
            """, as_dict = 1)
        routes = frappe.db.sql(f"""
                SELECT count(name)  as num_cnt, maintain_same_bus_bonus,route, shift from `tabManifest` where driver = '{doc.employee}' and date between '{doc.start_date}' and '{doc.end_date}' and docstatus = 1 group by route
            """, as_dict = 1)
        num_of_maintaince = 0
        payroll_pay =  frappe.get_cached_doc("Payroll Rule", data[-1].get('route'))
        total_mouthly_driver_amount = 0

        for manifest in manifests:
            total_mouthly_driver_amount += manifest.mouthly_driver_amount or 0
        # days_count = frappe.db.get_value("Shift Type", manifest.shift, "custom_days_count")

        if total_mouthly_driver_amount > 0:
            doc.append("earnings", {
                "salary_component": payroll_pay.table_baug[0].get('daily_end_of_month_salary_component'),
                "amount": total_mouthly_driver_amount

            })
        shifts = frappe.db.sql(f"""
                SELECT count(name)  as num_cnt, maintain_same_bus_bonus,route, shift, sum(total_revenue) as total_revenue from `tabManifest` where driver = '{doc.employee}' and date between '{doc.start_date}' and '{doc.end_date}' and docstatus = 1 group by shift 
            """, as_dict = 1)
        shift_types = frappe.db.sql(f"""
                SELECT name  as shift, custom_days_count as num_cnt , custom_types from `tabShift Type`  group by shift
            """, as_dict = 1)
        counts_dict = {row['shift']: row['num_cnt'] for row in shifts}
        shift_types_dict = {row['shift']: row['num_cnt'] for row in shift_types}
        _shift_types_dict = {row['shift']: {
            "custom_days_count": row['num_cnt'],
            "custom_types": row['custom_types'],
            } for row in shift_types}
        payroll_shift_dict = {row.shift_type: {
            "fixed_attendance_bonus": row.fixed_attendance_bonus,
            "regularity_salary_component": row.regularity_salary_component,
            "monthly_fixed_amount": row.monthly_fixed_amount,
            "monthly_percentage_": row.monthly_percentage_,
            "monthly_target": row.monthly_target,
            "daily_salary_component": row.daily_salary_component,
            "monthly_salary_component": row.monthly_salary_component,
            "extra_salary_component": row.extra_salary_component,
            "daily_end_of_month_salary_component":row.daily_end_of_month_salary_component
        } for row in payroll_pay.table_baug}
        # for shift, cus in shift_types_dict.items():
        totals = 0
        is_not_avg = False
        for min_shift in shifts:
            # frappe.throw(f"{_shift_types_dict}")
            if _shift_types_dict.get(min_shift.get('shift',{})).get('custom_types',{}):
                is_not_avg  = True
        monthly_target = 0
        monthly_percentage_ = 0
        monthly_fixed_amount = 0
        total_revenue = 0
        if not is_not_avg:
            for min_shift in shifts:
                monthly_target += payroll_shift_dict.get(min_shift.get('shift',{})).get('monthly_target', 0)
                monthly_percentage_ += payroll_shift_dict.get(min_shift.get('shift',{})).get('monthly_percentage_', 0)
                monthly_fixed_amount += payroll_shift_dict.get(min_shift.get('shift',{})).get('monthly_fixed_amount', 0)
                total_revenue += min_shift.get('total_revenue',0)
            frappe.throw(f'{shifts} :: {len(shifts)}')
            avg_monthly_target = monthly_target / len(shifts)
            avg_monthly_percentage_ = monthly_percentage_ / len(shifts)
            avg_monthly_fixed_amount = monthly_fixed_amount / len(shifts)
            amount_target = avg_monthly_fixed_amount
            if payroll_pay.payroll_calculation == "Percentage":
                if total_revenue >= avg_monthly_target:
                    amount_target = total_revenue * (avg_monthly_percentage_ / 100)
                else:
                    amount_target = 0
            if amount_target:
                doc.append("earnings", {
                            "salary_component": payroll_shift_dict.get(shifts[0].get('shift')).get('monthly_salary_component'),
                            "amount": amount_target
                            })
                data = get_employee_penalty(doc)

                # count_manifest = frappe.db.count('Manifest', {'driver': doc.employee, "date": ["Between", [doc.start_date, doc.end_date]],"docstatus": 1})
                counts = frappe.db.sql(f"""
                    SELECT count(name)  as num_cnt, shift from `tabManifest` where driver = '{doc.employee}' and date between '{doc.start_date}' and '{doc.end_date}' and docstatus = 1 group by shift
                """, as_dict = 1)
                
                counts_dict = {row['shift']: row['num_cnt'] for row in counts}
                penalty_setting = frappe.get_cached_doc('Penalty Settings')
                penalty_setting_dict = {row.shift_type: {"days":row.attendance_in_days,
                                                                    "deduction_percentage":row.deduction_percentage,} for row in penalty_setting.table_uean}
                for x in data:
                    emp_penalty = frappe.get_cached_doc('Employee Penalty', x.get('name'))
                    if penalty_setting.enable_drivers_deductions and not emp_penalty.is_discounted:
                        
                        if len(counts) == 1:
                            for shift, count in counts_dict.items():
                                    emp_penalty.penalty_amount = emp_penalty.penalty_amount - ( emp_penalty.penalty_amount *(penalty_setting_dict.get(shift).get('deduction_percentage') / 100))
                                    emp_penalty.is_discounted = 1
                                    emp_penalty.calculate_installments()
                                    emp_penalty.save()
                        if len(counts) > 1:
                            cnt = 0
                            for shift, count in counts_dict.items():
                                cnt += count
                            for shift, count in penalty_setting_dict.items():
                                    emp_penalty.penalty_amount = emp_penalty.penalty_amount - ( emp_penalty.penalty_amount *(penalty_setting_dict.get(shift).get('deduction_percentage') / 100))
                                    emp_penalty.is_discounted = 1
                                    emp_penalty.calculate_installments()
                                    emp_penalty.save()
            # frappe.throw(f"{payroll_shift_dict}")
        if is_not_avg:
            total_revenue = 0
            for min_shift in shifts:
                total_revenue += min_shift.get('total_revenue',0)
            for min_shift in shifts:
                if _shift_types_dict.get(min_shift.get('shift')).get('custom_types') == "Double Shift":
                    if min_shift.get('num_cnt')>= int(_shift_types_dict.get(min_shift.get('shift')).get('custom_days_count')):
                        monthly_target = payroll_shift_dict.get(min_shift.get('shift',{})).get('monthly_target', 0) * 2 
                        monthly_percentage_ = payroll_shift_dict.get(min_shift.get('shift',{})).get('monthly_percentage_', 0)
                        monthly_fixed_amount = payroll_shift_dict.get(min_shift.get('shift',{})).get('monthly_fixed_amount', 0)
                        amount_target = monthly_fixed_amount
                        
                        if payroll_pay.payroll_calculation == "Percentage":
                            amount_target = total_revenue * (monthly_percentage_ / 100)
                        doc.append("earnings", {
                        "salary_component": payroll_shift_dict.get(min_shift.get('shift')).get('monthly_salary_component'),
                        "amount": amount_target
                        })
                        # frappe.throw(f"{monthly_percentage_} {amount_target} HH1 ")

                elif _shift_types_dict.get(min_shift.get('shift')).get('custom_types') == "Long":
                    if min_shift.get('num_cnt')>= int(_shift_types_dict.get(min_shift.get('shift')).get('custom_days_count')):
                        monthly_target = payroll_shift_dict.get(min_shift.get('shift',{})).get('monthly_target', 0) 
                        monthly_percentage_ = payroll_shift_dict.get(min_shift.get('shift',{})).get('monthly_percentage_', 0)
                        monthly_fixed_amount = payroll_shift_dict.get(min_shift.get('shift',{})).get('monthly_fixed_amount', 0)
                        amount_target = monthly_fixed_amount
                        if payroll_pay.payroll_calculation == "Percentage":
                            amount_target = total_revenue * (monthly_percentage_ / 100)
                        doc.append("earnings", {
                        "salary_component": payroll_shift_dict.get(min_shift.get('shift')).get('monthly_salary_component'),
                        "amount": amount_target
                        })
                        pass
                        # frappe.throw(f"{monthly_percentage_} {amount_target} HH2")
                pass

            
            pass
            
        if len(shifts) > 1:
            for shift, count in counts_dict.items():
                if count >= shift_types_dict.get(shift):
                    doc.append("earnings", {
                        "salary_component": payroll_shift_dict.get(shift).get('regularity_salary_component'),
                        "amount": payroll_shift_dict.get(shift).get('fixed_attendance_bonus')
                        })
        for row in routes:
            pay_rule = frappe.get_cached_doc('Payroll Rule', row.get('route'))
            # frappe.throw(f'{row['num_cnt']}')
            if row.get('num_cnt') > 30:
                row['num_cnt']  = 30
            amount_basic = (pay_rule.fixed_salary_per_month / 30) * row.get('num_cnt')  
            doc.append("earnings", {
                            "salary_component":pay_rule.fixed_salary_component,
                            "amount": amount_basic
                            })
        # if len(shifts) > 1:
        #     for shift, count in counts_dict.items():
        #         if count >= shift_types_dict.get(shift):
        #             doc.append("earnings", {
        #                 "salary_component": payroll_shift_dict.get(shift).get('regularity_salary_component'),
        #                 "amount": payroll_shift_dict.get(shift).get('fixed_attendance_bonus')
        #                 })
            pass
        # if len(manifests) >= 26:
        #     doc.append("earnings", {
        #         "salary_component": "مكافأة انتظام",
        #         "amount": 700
        #     })
        
        for row in data:
            if row.get('maintain_same_bus_bonus'):
                num_of_maintaince += 1
        if data and len(data) == len(data) - num_of_maintaince:
            if doc.designation:
                designation = frappe.get_cached_doc('Designation', doc.designation)
                if designation.custom_not_applicable_for_driver_bonus:
                    doc.append("earnings", {
                        "salary_component": payroll_pay.same_bus_salary_component,
                        "amount": payroll_pay.fixed_same_bus_bonus
                    })

        # frappe.throw(f"{str(doc.earnings)}")
def before_insert(doc, method):
    adjustment_penalty(doc)
    get_deductions_amount(doc)
    pass
def on_submit(doc, method):
    if doc.custom_installment_deductions:
        for x in doc.custom_installment_deductions:
            frappe.db.sql(f"""Update `tabPenalty Schedule` SET is_accrued = 1 where name = '{x.get('row_schedule')}' """)
    pass
def get_employee_penalty(doc):
    data = frappe.db.sql(f"""
        SELECT name, salary_component ,is_a_term_penalty , penalty_amount FROM `tabEmployee Penalty` 
            where payment_start_date >= '{doc.start_date}' 
            and payment_start_date <='{doc.end_date}'  
            and employee= '{doc.employee}' and docstatus = 1
    """, as_dict =1)
    return data
def get_deductions_amount(doc):
    data = get_employee_penalty(doc)
    for x in data:
        if x.get(f"is_a_term_penalty", 0):
            principal_amount = frappe.db.sql(f"""SELECT name, payment_date, principal_amount from `tabPenalty Schedule` where parent = '{x.get('name')}' and is_accrued = 0 order by idx  """, as_dict = 1)
            doc.append('deductions',{
                'salary_component': x.get("salary_component"),
                'amount': principal_amount[0].get('principal_amount') if principal_amount else 0 
            })
            doc.append('custom_installment_deductions',{
                'payment_date': principal_amount[0].get('payment_date') ,
                'row_schedule': principal_amount[0].get('name') ,
                'amount': principal_amount[0].get('principal_amount')
            })
        else:
            doc.append('deductions',{
                'salary_component': x.get("salary_component"),
                'amount': x.get("penalty_amount")
            })
    pass
def adjustment_penalty(doc):
    data = get_employee_penalty(doc)

    # count_manifest = frappe.db.count('Manifest', {'driver': doc.employee, "date": ["Between", [doc.start_date, doc.end_date]],"docstatus": 1})
    counts = frappe.db.sql(f"""
        SELECT count(name)  as num_cnt, shift from `tabManifest` where driver = '{doc.employee}' and date between '{doc.start_date}' and '{doc.end_date}' and docstatus = 1 group by shift
    """, as_dict = 1)
    
    counts_dict = {row['shift']: row['num_cnt'] for row in counts}
    penalty_setting = frappe.get_cached_doc('Penalty Settings')
    penalty_setting_dict = {row.shift_type: {"days":row.attendance_in_days,
                                                        "deduction_percentage":row.deduction_percentage,} for row in penalty_setting.table_uean}
    for x in data:
        emp_penalty = frappe.get_cached_doc('Employee Penalty', x.get('name'))
        if penalty_setting.enable_drivers_deductions and not emp_penalty.is_discounted:
            
            if len(counts) == 1:
                for shift, count in counts_dict.items():
                    if count >= penalty_setting_dict.get(shift, {}).get('days',999999999999999999):
                        emp_penalty.penalty_amount = emp_penalty.penalty_amount - ( emp_penalty.penalty_amount *(penalty_setting_dict.get(shift).get('deduction_percentage') / 100))
                        emp_penalty.is_discounted = 1
                        emp_penalty.calculate_installments()
                        emp_penalty.save()
            if len(counts) > 1:
                cnt = 0
                for shift, count in counts_dict.items():
                    cnt += count
                for shift, count in penalty_setting_dict.items():
                    if cnt >= penalty_setting_dict.get(shift).get('days'):
                        emp_penalty.penalty_amount = emp_penalty.penalty_amount - ( emp_penalty.penalty_amount *(penalty_setting_dict.get(shift).get('deduction_percentage') / 100))
                        emp_penalty.is_discounted = 1
                        emp_penalty.calculate_installments()
                        emp_penalty.save()
                pass
    pass

def make_asset_item(doc, method):
    is_exist = frappe.db.exists("Item", doc.name, cache=True)

    if not is_exist:
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": doc.name,
            "item_group": "All Item Groups",
            "stock_uom": "Nos",
            "is_fixed_asset": 1,
            "is_stock_item": 0,
            "asset_category": "cars"
        })
        item.insert()
        asset = frappe.get_doc({
            "doctype": "Asset",
            "item_code": item.item_code,
            "location": doc.location,
            "is_existing_asset": 1,
            "gross_purchase_amount": doc.custom_price_vehicle or doc.vehicle_value,
            "asset_quantity": 1,
            "available_for_use_date": doc.creation,
            "company": doc.custom_company
        })
        asset.insert()

