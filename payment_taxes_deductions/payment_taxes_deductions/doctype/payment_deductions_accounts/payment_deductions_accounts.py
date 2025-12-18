# Copyright (c) 2025, abdopcnet@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class PaymentDeductionsAccounts(Document):
    pass


@frappe.whitelist()
def get_tax_accounts(company=None, customer_group=None):
    """
    Get all tax accounts from Payment Deductions Accounts based on company and customer_group
    Returns dictionary with all tax account names

    This is the unified source for tax account names.
    All account names come from Payment Deductions Accounts DocType.

    Args:
            company: Company name (optional, uses default company if not provided)
            customer_group: Customer Group name (optional, filters by company only if not provided)

    Returns:
            dict: Dictionary with tax_type as key and account name as value
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_global_default("company")

        if not company:
            frappe.throw(_("Company is required"))

        # Build filters: company is required, customer_group is optional
        filters = {"company": company}
        if customer_group:
            filters["customer_group"] = customer_group

        # Get account settings for this company and customer_group
        settings = frappe.get_value(
            "Payment Deductions Accounts",
            filters,
            [
                "commercial_profits",
                "regular_stamp",
                "additional_stamp",
                "contract_stamp",
                "check_stamp",
                "applied_professions_tax",
                "medical_professions_tax",
                "vat_20_percent",
                "vat_tax",
                "qaderon_difference",
            ],
            as_dict=True,
        )

        if settings:
            return {
                "commercial_profits": settings.commercial_profits or "",
                "regular_stamp": settings.regular_stamp or "",
                "additional_stamp": settings.additional_stamp or "",
                "contract_stamp": settings.contract_stamp or "",
                "check_stamp": settings.check_stamp or "",
                "applied_professions_tax": settings.applied_professions_tax or "",
                "medical_professions_tax": settings.medical_professions_tax or "",
                "vat_20_percent": settings.vat_20_percent or "",
                "vat_tax": settings.vat_tax or "",
                "qaderon_difference": settings.qaderon_difference or "",
            }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(),
                         _("Error getting tax accounts"))

    # Return empty dict if not found
    return {
        "commercial_profits": "",
        "regular_stamp": "",
        "additional_stamp": "",
        "contract_stamp": "",
        "check_stamp": "",
        "applied_professions_tax": "",
        "medical_professions_tax": "",
        "vat_20_percent": "",
        "vat_tax": "",
        "qaderon_difference": "",
    }


def get_tax_account(tax_type, company=None):
    """
    Get tax account name from Payment Deductions Accounts based on company
    Returns empty string if not found

    This is the unified source for tax account names.
    All account names come from Payment Deductions Accounts DocType.

    Args:
            tax_type: Type of tax (e.g., 'commercial_profits', 'regular_stamp', etc.)
            company: Company name (optional, uses default company if not provided)
            customer_group: Customer Group name (optional, filters by company only if not provided)

    Returns:
            str: Account name or empty string
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_global_default("company")

        if not company:
            return ""

        # Build filters: company is required, customer_group is optional
        filters = {"company": company}
        if customer_group:
            filters["customer_group"] = customer_group

        # Get account for this tax type, company and customer_group
        account = frappe.get_value(
            "Payment Deductions Accounts",
            filters,
            tax_type,
        )

        return account or ""

    except Exception as e:
        frappe.log_error(frappe.get_traceback(),
                         _("Error getting tax account"))
        return ""


def get_stamp_tax_rule(total, company=None):
    """
    Get stamp tax calculation rule for given total amount and company
    Returns the matching rule from Stamp Tax Calculation Rules DocType

    This is the unified source for tax calculation percentages and ranges.
    All percentages and ranges come from Stamp Tax Calculation Rules DocType.

    Args:
        total: Total amount to calculate tax for
        company: Company name (optional, uses default company if not provided)

    Returns:
        dict: Rule dictionary with all calculation parameters, or None if not found
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_global_default("company")

        if not company:
            return None

        # Get Stamp Tax Calculation Rules name for this company
        rules_name = frappe.db.get_value(
            "Stamp Tax Calculation Rules",
            {"company": company},
            "name"
        )

        if not rules_name:
            return None

        # Get Stamp Tax Calculation Rules document
        rules_doc = frappe.get_doc("Stamp Tax Calculation Rules", rules_name)

        if not rules_doc or not rules_doc.stamp_tax_range:
            return None

        # Find matching range
        total = flt(total)
        for range_row in rules_doc.stamp_tax_range:
            from_amount = flt(range_row.from_amount or 0)
            to_amount = flt(range_row.to_amount or 999999999)

            # Check if total falls within this range
            if from_amount <= total <= to_amount:
                return {
                    "from_amount": from_amount,
                    "to_amount": to_amount,
                    "percentage": flt(range_row.percentage or 0),
                    "subtract_amount": flt(range_row.subtract_amount or 0),
                    "add_amount": flt(range_row.add_amount or 0),
                    "check_stamp_amount": flt(range_row.check_stamp_amount or 0),
                    "ats_tax_amount": flt(range_row.ats_tax_amount or 0),
                    "additional_stamp_multiplier": flt(
                        range_row.additional_stamp_multiplier or 3
                    ),
                }

        return None

    except frappe.DoesNotExistError:
        # No rules found for this company
        return None
    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(), _("Error getting stamp tax rule")
        )
        return None


@frappe.whitelist()
def get_tax_accounts_by_customer_group(company=None, customer_group=None):
    """
    Get all tax accounts from Payment Deductions Accounts based on company and customer_group
    Returns dictionary with all tax account names

    Args:
        company: Company name (optional, uses default company if not provided)
        customer_group: Customer Group name (required)

    Returns:
        dict: Dictionary with tax_type as key and account name as value
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_global_default("company")

        if not company:
            frappe.throw(_("Company is required"))

        if not customer_group:
            frappe.throw(_("Customer Group is required"))

        # Get account settings for this company and customer_group
        settings = frappe.get_value(
            "Payment Deductions Accounts",
            {"company": company, "customer_group": customer_group},
            [
                "commercial_profits",
                "regular_stamp",
                "additional_stamp",
                "contract_stamp",
                "check_stamp",
                "applied_professions_tax",
                "medical_professions_tax",
                "vat_20_percent",
                "vat_tax",
                "qaderon_difference",
            ],
            as_dict=True,
        )

        if settings:
            return {
                "commercial_profits": settings.commercial_profits or "",
                "regular_stamp": settings.regular_stamp or "",
                "additional_stamp": settings.additional_stamp or "",
                "contract_stamp": settings.contract_stamp or "",
                "check_stamp": settings.check_stamp or "",
                "applied_professions_tax": settings.applied_professions_tax or "",
                "medical_professions_tax": settings.medical_professions_tax or "",
                "vat_20_percent": settings.vat_20_percent or "",
                "vat_tax": settings.vat_tax or "",
                "qaderon_difference": settings.qaderon_difference or "",
            }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(),
                         _("Error getting tax accounts by customer group"))

    # Return empty dict if not found
    return {
        "commercial_profits": "",
        "regular_stamp": "",
        "additional_stamp": "",
        "contract_stamp": "",
        "check_stamp": "",
        "applied_professions_tax": "",
        "medical_professions_tax": "",
        "vat_20_percent": "",
        "vat_tax": "",
        "qaderon_difference": "",
    }
