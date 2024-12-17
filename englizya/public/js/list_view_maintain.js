frappe.listview_settings['Maintenance'] = {
    get_indicator(doc) {
            // customize indicator color
            if (doc.status=="Approved") {
                return [__("Approved"), "green", "status,=,Approved"];
            } else {
                return [__("else"), "darkgrey", "status,=,else"];
            }
        },
    }