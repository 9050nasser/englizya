app_name = "englizya"
app_title = "Englizya"
app_publisher = "Mohammed Nasser"
app_description = "Englizya App"
app_email = "nasser@nasserx.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "englizya",
# 		"logo": "/assets/englizya/logo.png",
# 		"title": "Englizya",
# 		"route": "/englizya",
# 		"has_permission": "englizya.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/englizya/css/englizya.css"
# app_include_js = "/assets/englizya/js/englizya.js"

# include js, css files in header of web template
# web_include_css = "/assets/englizya/css/englizya.css"
# web_include_js = "/assets/englizya/js/englizya.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "englizya/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Payment Entry" : "public/js/pr.js",
	"Customer" : "public/js/customer.js",
	"Employee" : "public/js/employee.js",
	"Vehicle" : "public/js/vehicle.js",
              }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "englizya/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "englizya.utils.jinja_methods",
# 	"filters": "englizya.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "englizya.install.before_install"
# after_install = "englizya.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "englizya.uninstall.before_uninstall"
# after_uninstall = "englizya.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "englizya.utils.before_app_install"
# after_app_install = "englizya.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "englizya.utils.before_app_uninstall"
# after_app_uninstall = "englizya.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "englizya.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Serial and Batch Bundle": {
		"before_insert": "englizya.api.add_serials",
        
	},
    "Purchase Receipt": {
      "on_submit": "englizya.api.generate_tickets"  
	},
    "Salary Slip": {
      "before_insert": ["englizya.events.calculate_salary" ,
                        "englizya.events.before_insert"
                         ],
		"on_submit": ["englizya.events.on_submit" ,
                         ],
	},
    "Attendance":{
		"on_submit": "englizya.api.appliy_salary"  
	},
    "Vehicle":{
		"after_insert": ["englizya.triggers.vehicle.vehicle.after_insert",  "englizya.events.make_asset_item"] ,
		"validate": "englizya.triggers.vehicle.vehicle.validate"  ,
	},
    "Task":{
		"validate": "englizya.triggers.task.task.validate"  
	},
    "Stock Entry":{
		"on_submit": "englizya.triggers.stock_entry.stock_entry.on_submit"  
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"englizya.tasks.update_maintaince"
	],

}

# Testing
# -------

# before_tests = "englizya.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents" : "englizya.overrides.get_outstanding_reference_documents"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "englizya.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["englizya.utils.before_request"]
# after_request = ["englizya.utils.after_request"]

# Job Events
# ----------
# before_job = ["englizya.utils.before_job"]
# after_job = ["englizya.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"englizya.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
fixtures = [
    {"dt": "Custom Field", "filters": [
        [
            "module",
            "=",
            "Englizya"
        ]
    ]},
	{"dt": "Print Format", "filters": [
        [
            "module",
            "=",
            "Englizya"
        ]
    ]},
    {"dt": "Property Setter", "filters": [
        [
            "module",
            "=",
            "Englizya"
			
        ]
    ]},
    {"dt": "Workspace", "filters": [
        [
            "module",
            "=",
            "Englizya"
			
        ]
    ]},

]
