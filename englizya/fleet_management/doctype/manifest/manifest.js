// Copyright (c) 2024, Mohammed Nasser and contributors
// For license information, please see license.txt

frappe.ui.form.on("Manifest", {
    refresh(frm) {
        loadFontAwesome();
        frm.set_query("expenses", "details", function(){
            return {
                "filters": [
                    ["Expense Claim Type", "custom_for_manifest", "=", 1],
                ]
            }
        });
        frm.set_query("vehicle", function(){
            return {
                "filters": [
                    ["Vehicle", "custom_company", "=", frm.doc.company],
                ]
            }
        });
        frm.set_query("garage", function(){
            return {
                "filters": [
                    ["Branch", "custom_company", "=", frm.doc.company],
                ]
            }
        });
        if (frm.doc.docstatus==1) {
            frm.add_custom_button(__('View Ledger'), function () {
                // Redirect to General Ledger Report
                frappe.set_route('query-report', 'General Ledger', {
                    company: frm.doc.company,
                    voucher_no: frm.doc.name,
                    from_date: frm.doc.date,
                    to_date: frm.doc.date
                });
            }, __('View'));
        }
        if(frm.doc.docstatus === 0 && !frm.is_new()){
            frm.add_custom_button(__('Deduct Driver Amount'), function () {
                let dialog = new frappe.ui.Dialog({
                    title: 'Enter Deduction Amount',
                    fields: [
                        {
                            label: 'Amount',
                            fieldname: 'amount',
                            fieldtype: 'Float',
                        },
                        {
                            label: 'Reason',
                            fieldname: 'reason',
                            fieldtype: 'Data',
                            reqd: 1
                        },
                        {
                            label: 'Is Fully Deducted',
                            fieldname: 'is_fully_deducted',
                            fieldtype: 'Check'
                        }
                    ],
                    primary_action_label: __('Confirm'),
                    primary_action(values) {
                        if(values.is_fully_deducted){
                            frm.set_value("daily_driver_amount", 0)
                        } else {
                            if(values.amount != 0){
                                frm.set_value("daily_driver_amount", frm.doc.daily_driver_amount - values.amount)
                            }
                        }
                        if(values.is_fully_deducted || values.amount)
                            frm.set_value("deduction_reason", values.reason);
                        
                        // Close the dialog
                        dialog.hide();
                    }
                });
    
                // Show the dialog
                dialog.show();
            })
        }

            
        if (frm.doc.status == "Calculate") {
            frm.add_custom_button(__('<i class="fa-solid fa-plus fa-shake" style="color: #ffffff;"></i> New'), function () {
                let new_doc = frappe.model.get_new_doc("Manifest")
                    new_doc.shift = frm.doc.shift
                    new_doc.vehicle = frm.doc.vehicle
                    new_doc.driver = frm.doc.driver
                    new_doc.route = frm.doc.route
                    new_doc.old_manifest = frm.doc.old_manifest
                    
                    if (Array.isArray(frm.doc.table_fozg)) {
                        let filteredRows = frm.doc.table_fozg.filter(row => row.ticket_return_no > 0);
                    
                        filteredRows.forEach(row => {
                            let child = frappe.model.add_child(new_doc, "table_fozg");
                            child.letter = row.letter;
                            child.from = row.ticket_return_no;
                            fetch_ticket_details(frm, child);
                            calculate_total(frm);
                        });
                    
                        // Refresh the field to display the added rows, if necessary
                        frm.refresh_field("table_fozg");
                    }
                    
                    // Map the filtered rows to add child entries in `new_doc`

                    frappe.set_route("Form", "Manifest", new_doc.name);
            }).css({"color":"white", "background-color": "#008000", "font-weight": "800", "box-shadow": "0 0 20px rgba(0, 128, 0, 0.5)", "transition": "0.3s"}).hover(
                function() {
                    $(this).css("box-shadow", "0 0 40px rgba(0, 128, 0, 0.8)"); // Increase glow on hover
                },
                function() {
                    $(this).css("box-shadow", "0 0 20px rgba(0, 128, 0, 0.5)"); // Reset glow
                }
            );;
        }
        
    },
    onload(frm){
        if (frm.doc.status == "Calculate") {
            $.each(frm.fields_dict, function(fieldname, field) {
                frm.set_df_property(fieldname, 'read_only', 1);
            });
        }
    }
});

frappe.ui.form.on('Manifest', {
    refresh: function(frm) {
        calculate_total(frm);
    },
    items_add: function(frm) {
        calculate_total(frm);
    },
    items_remove: function(frm) {
        calculate_total(frm);
    },
    validate: function(frm) {
        calculate_total(frm);
    },
    // Trigger calculation when any amount field changes
    'table_fozg': function(frm, cdt, cdn) {
        calculate_total(frm);
    },
    'details': function(frm, cdt, cdn) {
        calculate_total(frm);
    },
    setup: function(frm, cdt, cdn) {
        calculate_total(frm);
    },
    onload: function(frm, cdt, cdn) {
        
        calculate_total(frm);
    },
    table_fozg_add: function(frm, cdt, cdn) {
        calculate_total(frm);
    },
    onload_post_render: function(frm, cdt, cdn) {
        calculate_total(frm);
    },
    before_save: function(frm, cdt, cdn) {
        calculate_total(frm);
    }
});

// Function to load Font Awesome
function loadFontAwesome() {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css'; // Update the version as needed
    document.head.appendChild(link);
}

// Call the function to load Font Awesome



function calculate_total(frm) {
    let total_amount = 0;
    let total_expenses = 0;
    let tickets_count = 0;
    frm.doc.table_fozg.forEach(item => {
        total_amount += item.net_total;
    });
    frm.doc.details.forEach(item => {
        total_expenses += item.value
    })
    frm.doc.table_fozg.forEach(item => {
        tickets_count += item.sold_tickets_count

    })
    console.log(tickets_count)
    frm.set_value('total_revenue', total_amount);  // 'total_amount' is the field in the parent DocType
    frm.set_value('total_expense', total_expenses);
    frm.set_value('net_total', (total_amount - total_expenses));
    frm.set_value('sold_tickets_count', tickets_count);
}

function fetch_ticket_details(frm, row) {
    if (frm.doc.driver) {
        if (row.letter && row.from) {
            row.ticket_return_no = 0
            row.total_return_ticket = 0
            frappe.call({
                method: 'englizya.api.get_ticket_details',
                args: {
                'batch': row.letter,
                'start_serial': row.from
                },
                callback: function(r) {
                if (r.message) {
                    console.log(r.message)
                    let res = r.message
                    if (res.status == "Sold") {
                        frappe.show_alert({
                            message:__(`This Ticket Book Sold`),
                            indicator:'blue'
                        }, 5);
                        frm.doc.table_fozg.pop()
                        frm.refresh_field("table_fozg")
                    } else {
                    row.from = res.returned_ticket > 0 ? res.returned_ticket : row.from
                    row.to = res.end_serial_no
                    row.category = res.category
                    row.registry_code = res.book_code
                    row.total_revenue = ((row.to - row.from + 1) * row.category)
                    row.net_total = ((row.to - row.from + 1) * row.category)
                    row.sold_tickets_count = (((row.to - row.from) +1) - (row.total_return_ticket || 0))
                    row.ticket_book = res.name
                    frm.refresh_field("table_fozg")
                    if (res.returned_ticket > 0) {
                        frappe.utils.play_sound("click");
                    frappe.show_alert({
                        message:__(`This Ticket Book Has Returned Ticket No ${res.returned_ticket}`),
                        indicator:'blue'
                    }, 5);
                    }
                    }
                
                } else {
                    frappe.utils.play_sound("error");
                    frappe.show_alert({
                        message:__("No Ticket Found With This Serial"),
                        indicator:'red'
                    }, 5);
                    

                }
                }
            });
            
        }
    } else {
        frm.set_value("table_fozg", [])
        frm.refresh_field("table_fozg")
        frappe.throw(__("Please Select Driver First"))

    }
}

frappe.ui.form.on("Custodies", "from", function (frm, cdt, cdn) {
    var row = locals[cdt][cdn]
    fetch_ticket_details(frm, row)
});

frappe.ui.form.on("Custodies", "ticket_return_no", function (frm, cdt, cdn) {
    var row = locals[cdt][cdn]
    if (row.ticket_return_no > row.from) {
        row.total_return_ticket = (row.to - row.ticket_return_no) + 1
        row.return_amount = ((row.to - row.ticket_return_no) + 1) * row.category
        row.net_total = row.total_revenue - row.return_amount
        row.sold_tickets_count = row.to - (row.total_return_ticket || 0)
        frm.refresh_field("table_fozg")
    } else if (row.ticket_return_no == 0) {
        row.total_return_ticket = 0
        row.return_amount = 0
        row.net_total = row.total_revenue - row.return_amount
        frm.refresh_field("table_fozg")
        
    } else if (row.ticket_return_no <= row.from) {
        frappe.throw(__("Ticket Return No Cannot be Smaller Than Ticket from No."))
    }
});
