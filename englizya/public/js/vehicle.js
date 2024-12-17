
frappe.ui.form.on("Vehicle", {
    refresh: function (frm) {
        if (frm.doc.license_plate) {
            frm.set_df_property('custom_plate_numbers', 'hidden', 1)
        }
        frm.set_query("customer", 'custom_details', function () {
            return {
                filters: [
                    ["custom_company", "=", frm.doc.custom_company],
                    ["disabled", "=", 0],
                ]
            };
        });
        frm.set_query("customer_group", 'custom_details', function () {
            return {
                filters: [
                    ["custom_is_specific_group", "=", 1],
                ]
            };
        });
    },

});

$(document).ready(function () {
    $('#one').on('input', function () {
        const field_value = $(this).val();
        const value = $(this).val().replace(/\d/g, '');
        $(this).val(value.slice(0, 1));
        if (typeof field_value === "string" && !/[^A-Za-z\u0600-\u06FF\s]/.test(field_value)) {
            console.log("Valid input, moving focus.");
            $('#two').focus();
        }
    });
    $('#two').on('input', function () {
        const field_value = $(this).val();
        const value = $(this).val().replace(/\d/g, '');
        $(this).val(value.slice(0, 1));
        if (typeof field_value === "string" && !/[^A-Za-z\u0600-\u06FF\s]/.test(field_value)) {
            console.log("Valid input, moving focus.");
            $('#three').focus();
        }
    });
    $('#three').on('input', function () {
        const field_value = $(this).val();
        const value = $(this).val().replace(/\d/g, '');
        $(this).val(value.slice(0, 1));
        if (typeof field_value === "string" && !/[^A-Za-z\u0600-\u06FF\s]/.test(field_value)) {
            console.log("Valid input, moving focus.");
            $('#four').focus();
        }
    });
    $('#four').on('input', function () {
        const value = $(this).val().replace(/\D/g, ''); // Remove non-numeric characters
        $(this).val(value.slice(0, 4)); // Limit to 4 digits
    });
});

$(document).ready(function () {
    // Function to send values to Frappe license_plate field in the same document
    function updateLicensePlate() {
        // Get the input values
        const inputOne = $('#one').val();
        const inputTwo = $('#two').val();
        const inputThree = $('#three').val();
        const inputFour = $('#four').val();

        // Combine the values into a single string (license plate)
        const licensePlate = `${inputOne} ${inputTwo} ${inputThree} ${inputFour}`

        // Update the 'license_plate' field in the Frappe form directly
        if (cur_frm) {
            cur_frm.set_value('license_plate', licensePlate); // Set value in the 'license_plate' field
            cur_frm.refresh_field('license_plate'); // Refresh the field to reflect the changes
        }
    }

    // Event listener for input changes to trigger real-time updates
    $('#one, #two, #three, #four').on('input', function () {
        updateLicensePlate(); // Call function on any input change
    });
});