
frappe.ui.form.on("Payment Entry", {
    custom_custom_get_outstanding_invoices: function (frm) {
		frm.events.get_outstanding_invoices_or_orders(frm, true, false);
	},
    get_outstanding_invoices_or_orders: function (frm, get_outstanding_invoices, get_orders_to_be_billed) {
		const today = frappe.datetime.get_today();
		let fields = [
			{ fieldtype: "Section Break", label: __("Posting Date") },
			{
				fieldtype: "Date",
				label: __("From Date"),
				fieldname: "from_posting_date",
				default: frappe.datetime.add_days(today, -30),
			},
			{ fieldtype: "Column Break" },
			{ fieldtype: "Date", label: __("To Date"), fieldname: "to_posting_date", default: today },
			{ fieldtype: "Section Break", label: __("Due Date") },
			{ fieldtype: "Date", label: __("From Date"), fieldname: "from_due_date" },
			{ fieldtype: "Column Break" },
			{ fieldtype: "Date", label: __("To Date"), fieldname: "to_due_date" },
			{ fieldtype: "Section Break", label: __("Outstanding Amount") },
			{
				fieldtype: "Float",
				label: __("Greater Than Amount"),
				fieldname: "outstanding_amt_greater_than",
				default: 0,
			},
			{ fieldtype: "Column Break" },
			{ fieldtype: "Float", label: __("Less Than Amount"), fieldname: "outstanding_amt_less_than" },
		];

		if (frm.dimension_filters) {
			let column_break_insertion_point = Math.ceil(frm.dimension_filters.length / 2);

			fields.push({ fieldtype: "Section Break" });
			frm.dimension_filters.map((elem, idx) => {
				fields.push({
					fieldtype: "Link",
					label: elem.document_type == "Cost Center" ? "Cost Center" : elem.label,
					options: elem.document_type,
					fieldname: elem.fieldname || elem.document_type,
				});
				if (idx + 1 == column_break_insertion_point) {
					fields.push({ fieldtype: "Column Break" });
				}
			});
		}

		fields = fields.concat([
			{ fieldtype: "Section Break" },
			{
				fieldtype: "Check",
				label: __("Allocate Payment Amount"),
				fieldname: "allocate_payment_amount",
				default: 1,
			},
		]);

		let btn_text = "";

		if (get_outstanding_invoices) {
			btn_text = "Get Outstanding Invoices";
		} else if (get_orders_to_be_billed) {
			btn_text = "Get Outstanding Orders";
		}

		frappe.prompt(
			fields,
			function (filters) {
				frappe.flags.allocate_payment_amount = true;
				frm.events.validate_filters_data(frm, filters);
				frm.doc.cost_center = filters.cost_center;
				frm.events.get_outstanding_documents(
					frm,
					filters,
					get_outstanding_invoices,
					get_orders_to_be_billed
				);
			},
			__("Filters"),
			__(btn_text)
		);
	},
	get_outstanding_documents: function (frm, filters, get_outstanding_invoices, get_orders_to_be_billed) {
        frm.clear_table("references");
    
        if (!frm.doc.party) {
            return;
        }
    
        frm.events.check_mandatory_to_fetch(frm);
        var company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;
    
        var args = {
            posting_date: frm.doc.posting_date,
            company: frm.doc.company,
            party_type: frm.doc.party_type,
            payment_type: frm.doc.payment_type,
            party: frm.doc.party,
            party_account: frm.doc.payment_type == "Receive" ? frm.doc.paid_from : frm.doc.paid_to,
            cost_center: frm.doc.cost_center,
        };
    
        for (let key in filters) {
            args[key] = filters[key];
        }
    
        if (get_outstanding_invoices) {
            args["get_outstanding_invoices"] = true;
        } else if (get_orders_to_be_billed) {
            args["get_orders_to_be_billed"] = true;
        }
    
        if (frm.doc.book_advance_payments_in_separate_party_account) {
            args["book_advance_payments_in_separate_party_account"] = true;
        }
    
        frappe.flags.allocate_payment_amount = filters["allocate_payment_amount"];
    
        return frappe.call({
            method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents",
            args: {
                args: args,
            },
            callback: function (r, rt) {
                if (r.message) {
                    var total_positive_outstanding = 0;
                    var total_negative_outstanding = 0;
                    $.each(r.message, function (i, d) {
                        var c = frm.add_child("references");
                        console.log("d", d)
                        c.reference_doctype = d.voucher_type;
                        c.reference_name = d.voucher_no;
                        c.due_date = d.due_date;
                        c.total_amount = d.invoice_amount;
                        c.outstanding_amount = d.outstanding_amount;
                        c.bill_no = d.bill_no;
                        c.payment_term = d.payment_term;
                        c.payment_term_outstanding = d.payment_term_outstanding;
                        c.allocated_amount = d.allocated_amount;
                        c.account = d.account;
                        c.custom_remarks = d.remarks;
    
                        if (!in_list(frm.events.get_order_doctypes(frm), d.voucher_type)) {
                            if (flt(d.outstanding_amount) > 0)
                                total_positive_outstanding += flt(d.outstanding_amount);
                            else total_negative_outstanding += Math.abs(flt(d.outstanding_amount));
                        }
    
                        var party_account_currency =
                            frm.doc.payment_type == "Receive"
                                ? frm.doc.paid_from_account_currency
                                : frm.doc.paid_to_account_currency;
    
                        if (party_account_currency != company_currency) {
                            c.exchange_rate = d.exchange_rate;
                        } else {
                            c.exchange_rate = 1;
                        }
                        if (in_list(frm.events.get_invoice_doctypes(frm), d.reference_doctype)) {
                            c.due_date = d.due_date;
                        }
                    });
    
                    if (
                        (frm.doc.payment_type == "Receive" && frm.doc.party_type == "Customer") ||
                        (frm.doc.payment_type == "Pay" && frm.doc.party_type == "Supplier") ||
                        (frm.doc.payment_type == "Pay" && frm.doc.party_type == "Employee")
                    ) {
                        if (total_positive_outstanding > total_negative_outstanding)
                            if (!frm.doc.paid_amount)
                                frm.set_value(
                                    "paid_amount",
                                    total_positive_outstanding - total_negative_outstanding
                                );
                    } else if (
                        total_negative_outstanding &&
                        total_positive_outstanding < total_negative_outstanding
                    ) {
                        if (!frm.doc.received_amount)
                            frm.set_value(
                                "received_amount",
                                total_negative_outstanding - total_positive_outstanding
                            );
                    }
                }
    
                frm.events.allocate_party_amount_against_ref_docs(
                    frm,
                    frm.doc.payment_type == "Receive" ? frm.doc.paid_amount : frm.doc.received_amount,
                    false
                );
            },
        });
    }
});
