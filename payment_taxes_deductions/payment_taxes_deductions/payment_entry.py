"""
Payment Entry Tax Calculations
Calculate and update tax amounts in Payment Entry taxes table

Structure:
1. Tax Calculation Functions (for taxes table)
2. Tax Calculation Functions (for API)
3. Contract Stamp Handling
4. VAT 20% Handling
5. Hook Functions (before_validate)
6. API Methods
"""

import frappe
from frappe import _
from frappe.utils import flt
from payment_taxes_deductions.payment_taxes_deductions.doctype.payment_deductions_accounts.payment_deductions_accounts import get_tax_account


# ============================================================================
# SECTION 1: TAX CALCULATION FUNCTIONS (FOR TAXES TABLE)
# ============================================================================
# Functions that update existing tax rows in the taxes table

def calculate_commercial_profits_tax(taxes, total, company=None):
    """
    Calculate commercial profits tax (ارباح تجارية)
    Tax rate: 1% if total > 300

    Args:
        taxes: Payment Entry taxes table
        total: Paid amount
        company: Company name
    """
    commercial_profits_account = get_tax_account("commercial_profits", company)
    if not commercial_profits_account:
        return

    for tax in taxes:
        if tax.account_head == commercial_profits_account and total > 300:
            tax.tax_amount = total * 0.01


def calculate_regular_stamp_tax(taxes, total, company=None):
    """
    Calculate regular stamp tax (دمغة عادية) based on total amount ranges
    Formula: ((total - 50) * percentage) / 4

    Args:
        taxes: Payment Entry taxes table
        total: Paid amount
        company: Company name
    """
    regular_stamp_account = get_tax_account("regular_stamp", company)
    if not regular_stamp_account:
        return

    regular_stamp_amount = 0

    # Calculate regular stamp based on total range
    if total in range(1, 51):
        regular_stamp_amount = 0
    elif total in range(51, 251):
        regular_stamp_amount = ((total - 50) * 0.048) / 4
    elif total in range(251, 501):
        regular_stamp_amount = ((total - 50) * 0.052) / 4
    elif total in range(501, 1001):
        regular_stamp_amount = ((total - 50) * 0.056) / 4
    elif total in range(1001, 5001):
        regular_stamp_amount = ((total - 50) * 0.06) / 4
    elif total in range(5001, 10001):
        regular_stamp_amount = ((total - 50) * 0.064) / 4
    elif total > 10000:
        regular_stamp_amount = ((total - 10050) * 0.024 + 640) / 4

    # Update regular stamp tax amount
    for tax in taxes:
        if tax.account_head == regular_stamp_account:
            tax.tax_amount = regular_stamp_amount


def calculate_additional_stamp_tax(taxes, total, company=None):
    """
    Calculate additional stamp tax (دمغة اضافية)
    Formula: regular_stamp_amount * 3

    Args:
        taxes: Payment Entry taxes table
        total: Paid amount
        company: Company name
    """
    additional_stamp_account = get_tax_account("additional_stamp", company)
    if not additional_stamp_account:
        return

    regular_stamp_amount = 0

    # Calculate regular stamp first (same logic as calculate_regular_stamp_tax)
    if total in range(1, 51):
        regular_stamp_amount = 0
    elif total in range(51, 251):
        regular_stamp_amount = ((total - 50) * 0.048) / 4
    elif total in range(251, 501):
        regular_stamp_amount = ((total - 50) * 0.052) / 4
    elif total in range(501, 1001):
        regular_stamp_amount = ((total - 50) * 0.056) / 4
    elif total in range(1001, 5001):
        regular_stamp_amount = ((total - 50) * 0.06) / 4
    elif total in range(5001, 10001):
        regular_stamp_amount = ((total - 50) * 0.064) / 4
    elif total > 10000:
        regular_stamp_amount = ((total - 10050) * 0.024 + 640) / 4

    # Additional stamp = regular stamp * 3
    additional_stamp_amount = regular_stamp_amount * 3

    # Update additional stamp tax amount
    for tax in taxes:
        if tax.account_head == additional_stamp_account:
            tax.tax_amount = additional_stamp_amount


# ============================================================================
# SECTION 2: TAX CALCULATION FUNCTIONS (FOR API)
# ============================================================================
# Functions that return calculated tax amounts (used by API method)

def calculate_commercial_profits(total):
    """
    Calculate commercial profits tax (الارباح التجارية)
    Tax rate: 1% if total > 300

    Args:
        total: Paid amount

    Returns:
        float: Commercial profits tax amount
    """
    if total > 300:
        return total * 0.01
    return 0


def calculate_regular_stamp(total):
    """
    Calculate regular stamp tax (الدمغة العادية) based on total amount ranges
    Formula: ((total - 50) * percentage) / 4

    Args:
        total: Paid amount

    Returns:
        float: Regular stamp tax amount
    """
    if total in range(1, 51):
        return 0
    elif total in range(51, 251):
        return ((total - 50) * 0.048) / 4
    elif total in range(251, 501):
        return ((total - 50) * 0.052) / 4
    elif total in range(501, 1001):
        return ((total - 50) * 0.056) / 4
    elif total in range(1001, 5001):
        return ((total - 50) * 0.06) / 4
    elif total in range(5001, 10001):
        return ((total - 50) * 0.064) / 4
    elif total > 10000:
        return ((total - 10050) * 0.024 + 640) / 4
    return 0


def calculate_additional_stamp(total):
    """
    Calculate additional stamp tax (الدمغة التدريجية)
    Formula: regular_stamp_amount * 3

    Args:
        total: Paid amount

    Returns:
        float: Additional stamp tax amount
    """
    regular_stamp = calculate_regular_stamp(total)
    return regular_stamp * 3


# ============================================================================
# SECTION 3: CONTRACT STAMP HANDLING
# ============================================================================

def handle_contract_stamp(doc, company=None):
    """
    Handle contract stamp (دمغة عقد) tax row
    Adds or updates contract stamp row based on contract_papers_qty
    Formula: contract_papers_qty * 3 * 0.90

    Args:
        doc: Payment Entry document
        company: Company name
    """
    contract_account = get_tax_account("contract_stamp", company)
    if not contract_account:
        return

    # Initialize taxes table if it doesn't exist
    if not doc.taxes:
        doc.taxes = []

    if doc.contract_papers_qty and doc.contract_papers_qty > 0:
        contract_amount = doc.contract_papers_qty * 3 * 0.90
        found = False

        # Update existing contract stamp row if found
        for tax in doc.taxes:
            if tax.account_head == contract_account:
                tax.tax_amount = contract_amount
                found = True
                break

        # Add new contract stamp row if not found
        if not found:
            doc.append("taxes", {
                "add_deduct_tax": "Deduct",
                "charge_type": "Actual",
                "account_head": contract_account,
                "tax_amount": contract_amount,
                "description": "دمغة عقد"
            })
    else:
        # Remove contract stamp rows if contract_papers_qty is 0 or empty
        doc.taxes = [
            tax for tax in doc.taxes if tax.account_head != contract_account]


# ============================================================================
# SECTION 4: VAT 20% HANDLING
# ============================================================================

def handle_vat_20_percent(doc, company=None):
    """
    Add VAT 20% tax row if Sales Invoice has VAT tax
    Formula: tax_inv.tax_amount * 0.20

    Args:
        doc: Payment Entry document
        company: Company name
    """
    vat_20_account = get_tax_account("vat_20_percent", company)
    vat_tax_account = get_tax_account("vat_tax", company)

    if not vat_20_account or not vat_tax_account:
        return

    # Initialize taxes table if it doesn't exist
    if not doc.taxes:
        doc.taxes = []

    # Check if VAT 20% row already exists
    vat_exists = any(tax.account_head == vat_20_account for tax in doc.taxes)

    if not vat_exists:
        # Process all references to find VAT tax
        for ref in doc.references:
            if ref.reference_name and ref.reference_doctype == "Sales Invoice":
                try:
                    inv = frappe.get_doc(
                        ref.reference_doctype, ref.reference_name)
                    for tax_inv in inv.taxes:
                        if tax_inv.account_head == vat_tax_account:
                            doc.append("taxes", {
                                "add_deduct_tax": "Deduct",
                                "charge_type": "Actual",
                                "account_head": vat_20_account,
                                "tax_amount": tax_inv.tax_amount * 0.20,
                                "description": "20% من القيمة المضافة"
                            })
                            vat_exists = True
                            break
                    if vat_exists:
                        break
                except frappe.DoesNotExistError:
                    continue


# ============================================================================
# SECTION 5: HOOK FUNCTIONS
# ============================================================================

def before_validate(doc, method=None):
    """
    Calculate and update tax amounts before Payment Entry validation
    Runs automatically when Payment Entry is saved

    Args:
        doc: Payment Entry document
        method: Method name (not used, required for hooks)
    """
    # Get company from Payment Entry
    company = doc.company or frappe.defaults.get_global_default("company")

    # Handle contract stamp first (works even if taxes table is empty)
    handle_contract_stamp(doc, company)

    # Initialize taxes table if it doesn't exist
    if not doc.taxes:
        doc.taxes = []

    total = flt(doc.paid_amount or 0)

    # Calculate commercial profits tax
    calculate_commercial_profits_tax(doc.taxes, total, company)

    # Calculate regular stamp tax
    calculate_regular_stamp_tax(doc.taxes, total, company)

    # Calculate additional stamp tax
    calculate_additional_stamp_tax(doc.taxes, total, company)

    # Handle VAT 20%
    handle_vat_20_percent(doc, company)


# ============================================================================
# SECTION 6: API METHODS
# ============================================================================

@frappe.whitelist()
def test(total):
    """
    API method to calculate tax amounts for Payment Entry
    Called by client script when "حساب الضرائب والدمغات" button is clicked

    Args:
        total: Paid amount (from frappe.form_dict)

    Returns:
        list: List with dictionary containing calculated tax amounts
    """
    try:
        # Convert total to float
        total = flt(total or 0)

        # Calculate tax amounts
        atvat = calculate_commercial_profits(total)
        normal_damgha = calculate_regular_stamp(total)
        tadregya_damgha = calculate_additional_stamp(total)

        # Return response in expected format
        return [{
            "الارباح التجارية": atvat,
            "الدمغة العادية": normal_damgha,
            "الدمغة التدريجية": tadregya_damgha
        }]

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error in test API method"))
        frappe.throw(_("Error calculating taxes: {0}").format(str(e)))
