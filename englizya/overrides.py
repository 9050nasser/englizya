import frappe
import json

import json
from functools import reduce

import frappe
from frappe import _,qb

from frappe.utils import getdate, nowdate


import erpnext
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_dimensions

from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account

from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import (
    get_account_currency,
    get_held_invoices,
)
from erpnext.controllers.accounts_controller import (
    get_supplier_block_status,
)
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.doctype.payment_entry.payment_entry import split_invoices_based_on_payment_terms, get_negative_outstanding_invoices, get_orders_to_be_billed
from frappe.utils import (
    flt,
    getdate,
    nowdate,
)
from json import loads
from typing import TYPE_CHECKING, Optional

import frappe
import frappe.defaults
from frappe import _, qb, throw
from frappe.model.meta import get_field_precision
from frappe.query_builder import AliasedQuery, Criterion, Table
from frappe.query_builder.functions import Count, Sum
from frappe.query_builder.utils import DocType
from frappe.utils import (
    add_days,
    cint,
    create_batch,
    cstr,
    flt,
    formatdate,
    get_datetime,
    get_number_format_info,
    getdate,
    now,
    nowdate,
)
from pypika import Order
from pypika.terms import ExistsCriterion

import erpnext

# imported to enable erpnext.accounts.utils.get_account_currency
from erpnext.accounts.doctype.account.account import get_account_currency
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_dimensions
from erpnext.stock import get_warehouse_account_map
from erpnext.stock.utils import get_stock_value_on
@frappe.whitelist()
def get_outstanding_reference_documents(args, validate=False):
    if isinstance(args, str):
        args = json.loads(args)

    if args.get("party_type") == "Member":
        return

    if not args.get("get_outstanding_invoices") and not args.get("get_orders_to_be_billed"):
        args["get_outstanding_invoices"] = True

    ple = qb.DocType("Payment Ledger Entry")
    common_filter = []
    accounting_dimensions_filter = []
    posting_and_due_date = []

    # confirm that Supplier is not blocked
    if args.get("party_type") == "Supplier":
        supplier_status = get_supplier_block_status(args["party"])
        if supplier_status["on_hold"]:
            if supplier_status["hold_type"] == "All":
                return []
            elif supplier_status["hold_type"] == "Payments":
                if (
                    not supplier_status["release_date"]
                    or getdate(nowdate()) <= supplier_status["release_date"]
                ):
                    return []

    party_account_currency = get_account_currency(args.get("party_account"))
    company_currency = frappe.get_cached_value("Company", args.get("company"), "default_currency")

    # Get positive outstanding sales /purchase invoices
    condition = ""
    if args.get("voucher_type") and args.get("voucher_no"):
        condition = " and voucher_type={} and voucher_no={}".format(
            frappe.db.escape(args["voucher_type"]), frappe.db.escape(args["voucher_no"])
        )
        common_filter.append(ple.voucher_type == args["voucher_type"])
        common_filter.append(ple.voucher_no == args["voucher_no"])

    # Add cost center condition
    if args.get("cost_center"):
        condition += " and cost_center='%s'" % args.get("cost_center")
        accounting_dimensions_filter.append(ple.cost_center == args.get("cost_center"))

    # dynamic dimension filters
    active_dimensions = get_dimensions()[0]
    for dim in active_dimensions:
        if args.get(dim.fieldname):
            condition += f" and {dim.fieldname}='{args.get(dim.fieldname)}'"
            accounting_dimensions_filter.append(ple[dim.fieldname] == args.get(dim.fieldname))

    date_fields_dict = {
        "posting_date": ["from_posting_date", "to_posting_date"],
        "due_date": ["from_due_date", "to_due_date"],
    }

    for fieldname, date_fields in date_fields_dict.items():
        if args.get(date_fields[0]) and args.get(date_fields[1]):
            condition += " and {} between '{}' and '{}'".format(
                fieldname, args.get(date_fields[0]), args.get(date_fields[1])
            )
            posting_and_due_date.append(ple[fieldname][args.get(date_fields[0]) : args.get(date_fields[1])])
        elif args.get(date_fields[0]):
            # if only from date is supplied
            condition += f" and {fieldname} >= '{args.get(date_fields[0])}'"
            posting_and_due_date.append(ple[fieldname].gte(args.get(date_fields[0])))
        elif args.get(date_fields[1]):
            # if only to date is supplied
            condition += f" and {fieldname} <= '{args.get(date_fields[1])}'"
            posting_and_due_date.append(ple[fieldname].lte(args.get(date_fields[1])))

    if args.get("company"):
        condition += " and company = {}".format(frappe.db.escape(args.get("company")))
        common_filter.append(ple.company == args.get("company"))

    outstanding_invoices = []
    negative_outstanding_invoices = []

    if args.get("book_advance_payments_in_separate_party_account"):
        party_account = get_party_account(args.get("party_type"), args.get("party"), args.get("company"))
    else:
        party_account = args.get("party_account")

    if args.get("get_outstanding_invoices"):
        outstanding_invoices = get_outstanding_invoices(
            args.get("party_type"),
            args.get("party"),
            [party_account],
            common_filter=common_filter,
            posting_date=posting_and_due_date,
            min_outstanding=args.get("outstanding_amt_greater_than"),
            max_outstanding=args.get("outstanding_amt_less_than"),
            accounting_dimensions=accounting_dimensions_filter,
            vouchers=args.get("vouchers") or None,
        )

        outstanding_invoices = split_invoices_based_on_payment_terms(
            outstanding_invoices, args.get("company")
        )

        for d in outstanding_invoices:
            d["exchange_rate"] = 1
            if party_account_currency != company_currency:
                if d.voucher_type in frappe.get_hooks("invoice_doctypes"):
                    d["exchange_rate"] = frappe.db.get_value(d.voucher_type, d.voucher_no, "conversion_rate")
                elif d.voucher_type == "Journal Entry":
                    d["exchange_rate"] = get_exchange_rate(
                        party_account_currency, company_currency, d.posting_date
                    )
            if d.voucher_type in ("Purchase Invoice"):
                d["bill_no"] = frappe.db.get_value(d.voucher_type, d.voucher_no, "bill_no")

        # Get negative outstanding sales /purchase invoices
        if args.get("party_type") != "Employee":
            negative_outstanding_invoices = get_negative_outstanding_invoices(
                args.get("party_type"),
                args.get("party"),
                args.get("party_account"),
                party_account_currency,
                company_currency,
                condition=condition,
            )

    # Get all SO / PO which are not fully billed or against which full advance not paid
    orders_to_be_billed = []
    if args.get("get_orders_to_be_billed"):
        orders_to_be_billed = get_orders_to_be_billed(
            args.get("posting_date"),
            args.get("party_type"),
            args.get("party"),
            args.get("company"),
            party_account_currency,
            company_currency,
            filters=args,
        )

    data = negative_outstanding_invoices + outstanding_invoices + orders_to_be_billed

    if not data:
        if args.get("get_outstanding_invoices") and args.get("get_orders_to_be_billed"):
            ref_document_type = "invoices or orders"
        elif args.get("get_outstanding_invoices"):
            ref_document_type = "invoices"
        elif args.get("get_orders_to_be_billed"):
            ref_document_type = "orders"

        if not validate:
            frappe.msgprint(
                _(
                    "No outstanding {0} found for the {1} {2} which qualify the filters you have specified."
                ).format(
                    _(ref_document_type), _(args.get("party_type")).lower(), frappe.bold(args.get("party"))
                )
            )

    return data

def get_outstanding_invoices(
    party_type,
    party,
    account,
    common_filter=None,
    posting_date=None,
    min_outstanding=None,
    max_outstanding=None,
    accounting_dimensions=None,
    vouchers=None,  # list of dicts [{'voucher_type': '', 'voucher_no': ''}] for filtering
    limit=None,  # passed by reconciliation tool
    voucher_no=None,  # filter passed by reconciliation tool
):
    ple = qb.DocType("Payment Ledger Entry")
    outstanding_invoices = []
    precision = frappe.get_precision("Sales Invoice", "outstanding_amount") or 2

    if account:
        root_type, account_type = frappe.get_cached_value(
            "Account", account[0], ["root_type", "account_type"]
        )
        party_account_type = "Receivable" if root_type == "Asset" else "Payable"
        party_account_type = account_type or party_account_type
    else:
        party_account_type = erpnext.get_party_account_type(party_type)

    held_invoices = get_held_invoices(party_type, party)

    common_filter = common_filter or []
    common_filter.append(ple.account_type == party_account_type)
    common_filter.append(ple.account.isin(account))
    common_filter.append(ple.party_type == party_type)
    common_filter.append(ple.party == party)

    ple_query = QueryPaymentLedger()
    invoice_list = ple_query.get_voucher_outstandings(
        vouchers=vouchers,
        common_filter=common_filter,
        posting_date=posting_date,
        min_outstanding=min_outstanding,
        max_outstanding=max_outstanding,
        get_invoices=True,
        accounting_dimensions=accounting_dimensions or [],
        limit=limit,
        voucher_no=voucher_no,
    )

    for d in invoice_list:
        payment_amount = d.invoice_amount_in_account_currency - d.outstanding_in_account_currency
        outstanding_amount = d.outstanding_in_account_currency
        if outstanding_amount > 0.5 / (10**precision):
            if (
                min_outstanding
                and max_outstanding
                and not (outstanding_amount >= min_outstanding and outstanding_amount <= max_outstanding)
            ):
                continue

            if not d.voucher_type == "Purchase Invoice" or d.voucher_no not in held_invoices:
                outstanding_invoices.append(
                    frappe._dict(
                        {
                            "voucher_no": d.voucher_no,
                            "voucher_type": d.voucher_type,
                            "posting_date": d.posting_date,
                            "invoice_amount": flt(d.invoice_amount_in_account_currency),
                            "payment_amount": payment_amount,
                            "outstanding_amount": outstanding_amount,
                            "due_date": d.due_date,
                            "currency": d.currency,
                            "account": d.account,
                            "remarks": d.remarks,
                        }
                    )
                )

    outstanding_invoices = sorted(outstanding_invoices, key=lambda k: k["due_date"] or getdate(nowdate()))
    return outstanding_invoices

class QueryPaymentLedger:
    """
    Helper Class for Querying Payment Ledger Entry
    """

    def __init__(self):
        self.ple = qb.DocType("Payment Ledger Entry")

        # query result
        self.voucher_outstandings = []

        # query filters
        self.vouchers = []
        self.common_filter = []
        self.voucher_posting_date = []
        self.min_outstanding = None
        self.max_outstanding = None
        self.limit = self.voucher_no = None

    def reset(self):
        # clear filters
        self.vouchers.clear()
        self.common_filter.clear()
        self.min_outstanding = self.max_outstanding = self.limit = None

        # clear result
        self.voucher_outstandings.clear()

    def query_for_outstanding(self):
        """
        Database query to fetch voucher amount and voucher outstanding using Common Table Expression
        """

        ple = self.ple

        filter_on_voucher_no = []
        filter_on_against_voucher_no = []

        if self.vouchers:
            voucher_types = set([x.voucher_type for x in self.vouchers])
            voucher_nos = set([x.voucher_no for x in self.vouchers])

            filter_on_voucher_no.append(ple.voucher_type.isin(voucher_types))
            filter_on_voucher_no.append(ple.voucher_no.isin(voucher_nos))

            filter_on_against_voucher_no.append(ple.against_voucher_type.isin(voucher_types))
            filter_on_against_voucher_no.append(ple.against_voucher_no.isin(voucher_nos))

        if self.voucher_no:
            filter_on_voucher_no.append(ple.voucher_no.like(f"%{self.voucher_no}%"))
            filter_on_against_voucher_no.append(ple.against_voucher_no.like(f"%{self.voucher_no}%"))

        # build outstanding amount filter
        filter_on_outstanding_amount = []
        if self.min_outstanding:
            if self.min_outstanding > 0:
                filter_on_outstanding_amount.append(
                    Table("outstanding").amount_in_account_currency >= self.min_outstanding
                )
            else:
                filter_on_outstanding_amount.append(
                    Table("outstanding").amount_in_account_currency <= self.min_outstanding
                )
        if self.max_outstanding:
            if self.max_outstanding > 0:
                filter_on_outstanding_amount.append(
                    Table("outstanding").amount_in_account_currency <= self.max_outstanding
                )
            else:
                filter_on_outstanding_amount.append(
                    Table("outstanding").amount_in_account_currency >= self.max_outstanding
                )

        if self.limit and self.get_invoices:
            outstanding_vouchers = (
                qb.from_(ple)
                .select(
                    ple.against_voucher_no.as_("voucher_no"),
                    Sum(ple.amount_in_account_currency).as_("amount_in_account_currency"),
                )
                .where(ple.delinked == 0)
                .where(Criterion.all(filter_on_against_voucher_no))
                .where(Criterion.all(self.common_filter))
                .where(Criterion.all(self.dimensions_filter))
                .where(Criterion.all(self.voucher_posting_date))
                .groupby(ple.against_voucher_type, ple.against_voucher_no, ple.party_type, ple.party)
                .orderby(ple.posting_date, ple.voucher_no)
                .having(qb.Field("amount_in_account_currency") > 0)
                .limit(self.limit)
                .run()
            )
            if outstanding_vouchers:
                filter_on_voucher_no.append(ple.voucher_no.isin([x[0] for x in outstanding_vouchers]))
                filter_on_against_voucher_no.append(
                    ple.against_voucher_no.isin([x[0] for x in outstanding_vouchers])
                )

        # build query for voucher amount
        query_voucher_amount = (
            qb.from_(ple)
            .select(
                ple.account,
                ple.voucher_type,
                ple.voucher_no,
                ple.party_type,
                ple.party,
                ple.posting_date,
                ple.due_date,
                ple.remarks,
                ple.account_currency.as_("currency"),
                ple.cost_center.as_("cost_center"),
                Sum(ple.amount).as_("amount"),
                Sum(ple.amount_in_account_currency).as_("amount_in_account_currency"),
            )
            .where(ple.delinked == 0)
            .where(Criterion.all(filter_on_voucher_no))
            .where(Criterion.all(self.common_filter))
            .where(Criterion.all(self.dimensions_filter))
            .where(Criterion.all(self.voucher_posting_date))
            .groupby(ple.voucher_type, ple.voucher_no, ple.party_type, ple.party)
        )

        # build query for voucher outstanding
        query_voucher_outstanding = (
            qb.from_(ple)
            .select(
                ple.account,
                ple.against_voucher_type.as_("voucher_type"),
                ple.against_voucher_no.as_("voucher_no"),
                ple.party_type,
                ple.party,
                ple.posting_date,
                ple.due_date,
                ple.remarks,
                ple.account_currency.as_("currency"),
                Sum(ple.amount).as_("amount"),
                Sum(ple.amount_in_account_currency).as_("amount_in_account_currency"),
            )
            .where(ple.delinked == 0)
            .where(Criterion.all(filter_on_against_voucher_no))
            .where(Criterion.all(self.common_filter))
            .groupby(ple.against_voucher_type, ple.against_voucher_no, ple.party_type, ple.party)
        )

        # build CTE for combining voucher amount and outstanding
        self.cte_query_voucher_amount_and_outstanding = (
            qb.with_(query_voucher_amount, "vouchers")
            .with_(query_voucher_outstanding, "outstanding")
            .from_(AliasedQuery("vouchers"))
            .left_join(AliasedQuery("outstanding"))
            .on(
                (AliasedQuery("vouchers").account == AliasedQuery("outstanding").account)
                & (AliasedQuery("vouchers").voucher_type == AliasedQuery("outstanding").voucher_type)
                & (AliasedQuery("vouchers").voucher_no == AliasedQuery("outstanding").voucher_no)
                & (AliasedQuery("vouchers").party_type == AliasedQuery("outstanding").party_type)
                & (AliasedQuery("vouchers").party == AliasedQuery("outstanding").party)
            )
            .select(
                Table("vouchers").account,
                Table("vouchers").voucher_type,
                Table("vouchers").voucher_no,
                Table("vouchers").party_type,
                Table("vouchers").party,
                Table("vouchers").posting_date,
                Table("vouchers").amount.as_("invoice_amount"),
                Table("vouchers").amount_in_account_currency.as_("invoice_amount_in_account_currency"),
                Table("outstanding").amount.as_("outstanding"),
                Table("outstanding").amount_in_account_currency.as_("outstanding_in_account_currency"),
                (Table("vouchers").amount - Table("outstanding").amount).as_("paid_amount"),
                (
                    Table("vouchers").amount_in_account_currency
                    - Table("outstanding").amount_in_account_currency
                ).as_("paid_amount_in_account_currency"),
                Table("vouchers").due_date,
                Table("vouchers").currency,
                Table("vouchers").remarks,
                Table("vouchers").cost_center.as_("cost_center"),
            )
            .where(Criterion.all(filter_on_outstanding_amount))
        )

        # build CTE filter
        # only fetch invoices
        if self.get_invoices:
            self.cte_query_voucher_amount_and_outstanding = (
                self.cte_query_voucher_amount_and_outstanding.having(
                    qb.Field("outstanding_in_account_currency") > 0
                )
            )
        # only fetch payments
        elif self.get_payments:
            self.cte_query_voucher_amount_and_outstanding = (
                self.cte_query_voucher_amount_and_outstanding.having(
                    qb.Field("outstanding_in_account_currency") < 0
                )
            )

        if self.limit:
            self.cte_query_voucher_amount_and_outstanding = (
                self.cte_query_voucher_amount_and_outstanding.limit(self.limit)
            )

        # execute SQL
        self.voucher_outstandings = self.cte_query_voucher_amount_and_outstanding.run(as_dict=True)

    def get_voucher_outstandings(
        self,
        vouchers=None,
        common_filter=None,
        posting_date=None,
        min_outstanding=None,
        max_outstanding=None,
        get_payments=False,
        get_invoices=False,
        accounting_dimensions=None,
        limit=None,
        voucher_no=None,
    ):
        """
        Fetch voucher amount and outstanding amount from Payment Ledger using Database CTE

        vouchers - dict of vouchers to get
        common_filter - array of criterions
        min_outstanding - filter on minimum total outstanding amount
        max_outstanding - filter on maximum total  outstanding amount
        get_invoices - only fetch vouchers(ledger entries with +ve outstanding)
        get_payments - only fetch payments(ledger entries with -ve outstanding)
        """

        self.reset()
        self.vouchers = vouchers
        self.common_filter = common_filter or []
        self.dimensions_filter = accounting_dimensions or []
        self.voucher_posting_date = posting_date or []
        self.min_outstanding = min_outstanding
        self.max_outstanding = max_outstanding
        self.get_payments = get_payments
        self.get_invoices = get_invoices
        self.limit = limit
        self.voucher_no = voucher_no
        self.query_for_outstanding()
        return self.voucher_outstandings

