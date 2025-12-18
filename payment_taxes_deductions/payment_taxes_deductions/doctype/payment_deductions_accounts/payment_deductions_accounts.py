# Copyright (c) 2025, abdopcnet@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PaymentDeductionsAccounts(Document):
    pass


@frappe.whitelist()
def get_tax_accounts(company=None):
    """
    Get all tax accounts from Payment Deductions Accounts based on company
    Returns dictionary with all tax account names

    Args:
            company: Company name (optional, uses default company if not provided)

    Returns:
            dict: Dictionary with tax_type as key and account name as value
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_global_default("company")

        if not company:
            frappe.throw(_("Company is required"))

        # Get account settings for this company
        settings = frappe.get_value(
            "Payment Deductions Accounts",
            {"company": company},
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

    Args:
            tax_type: Type of tax (e.g., 'commercial_profits', 'regular_stamp', etc.)
            company: Company name (optional, uses default company if not provided)

    Returns:
            str: Account name or empty string
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_global_default("company")

        if not company:
            return ""

        # Get account for this tax type and company
        account = frappe.get_value(
            "Payment Deductions Accounts",
            {"company": company},
            tax_type,
        )

        return account or ""

    except Exception as e:
        frappe.log_error(frappe.get_traceback(),
                         _("Error getting tax account"))
        return ""
