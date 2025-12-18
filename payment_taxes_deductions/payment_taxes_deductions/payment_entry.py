"""
Payment Entry Tax Calculations
Calculate and update tax amounts in Payment Entry taxes table

Uses unified structure:
- Payment Deductions Accounts: For tax account names (get_tax_account)
- Stamp Tax Calculation Rules: For tax calculation percentages/ranges (get_stamp_tax_rule)

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
from payment_taxes_deductions.payment_taxes_deductions.doctype.payment_deductions_accounts.payment_deductions_accounts import (
    get_tax_account,
    get_stamp_tax_rule
)


# ============================================================================
# SECTION 1: TAX CALCULATION FUNCTIONS (FOR TAXES TABLE)
# ============================================================================
# Functions that update existing tax rows in the taxes table

def calculate_commercial_profits_tax(taxes, total, company=None, customer_group=None):
    """
    Calculate commercial profits tax (ارباح تجارية)
    Tax rate: 1% if total > 300

    Args:
        taxes: Payment Entry taxes table
        total: Paid amount
        company: Company name
        customer_group: Customer Group name (optional, for filtering accounts)
    """
    commercial_profits_account = get_tax_account(
        "commercial_profits", company, customer_group)
    if not commercial_profits_account:
        return

    for tax in taxes:
        if tax.account_head == commercial_profits_account and total > 300:
            tax.tax_amount = total * 0.01


def calculate_regular_stamp_tax(taxes, total, company=None, customer_group=None):
    """
    Calculate regular stamp tax (دمغة عادية) based on rules from Stamp Tax Calculation Rules DocType
    Formula: ((total - subtract_amount) * percentage / 100 + add_amount) / 4

    Args:
        taxes: Payment Entry taxes table
        total: Paid amount
        company: Company name
        customer_group: Customer Group name (optional, for filtering accounts)
    """
    regular_stamp_account = get_tax_account(
        "regular_stamp", company, customer_group)
    if not regular_stamp_account:
        return

    # Get rule from DocType
    rule = get_stamp_tax_rule(total, company)

    if not rule:
        frappe.throw(
            _("No stamp tax calculation rule found for company {0} and amount {1}. Please configure Stamp Tax Calculation Rules.").format(
                company or _("Unknown"), total
            )
        )

    # Use rule from DocType
    regular_stamp_amount = (
        (total - rule["subtract_amount"]) * rule["percentage"] / 100
        + rule["add_amount"]
    ) / 4

    # Update regular stamp tax amount
    for tax in taxes:
        if tax.account_head == regular_stamp_account:
            tax.tax_amount = regular_stamp_amount


def calculate_additional_stamp_tax(taxes, total, company=None, customer_group=None):
    """
    Calculate additional stamp tax (دمغة اضافية)
    Formula: regular_stamp_amount * multiplier (from rule)

    Args:
        taxes: Payment Entry taxes table
        total: Paid amount
        company: Company name
        customer_group: Customer Group name (optional, for filtering accounts)
    """
    additional_stamp_account = get_tax_account(
        "additional_stamp", company, customer_group)
    if not additional_stamp_account:
        return

    # Get rule from DocType
    rule = get_stamp_tax_rule(total, company)

    if not rule:
        frappe.throw(
            _("No stamp tax calculation rule found for company {0} and amount {1}. Please configure Stamp Tax Calculation Rules.").format(
                company or _("Unknown"), total
            )
        )

    # Calculate regular stamp using rule from DocType
    regular_stamp_amount = (
        (total - rule["subtract_amount"]) * rule["percentage"] / 100
        + rule["add_amount"]
    ) / 4

    # Additional stamp = regular stamp * multiplier
    multiplier = rule["additional_stamp_multiplier"]
    additional_stamp_amount = regular_stamp_amount * multiplier

    # Update additional stamp tax amount
    for tax in taxes:
        if tax.account_head == additional_stamp_account:
            tax.tax_amount = additional_stamp_amount


def handle_check_stamp_and_ats_tax(doc, total, company=None, customer_group=None):
    """
    Handle check stamp (دمغة شيك) and ATS tax (ضرائب أ ت ص) from rules
    These are fixed amounts that apply only to specific ranges

    Args:
        doc: Payment Entry document
        total: Paid amount
        company: Company name
        customer_group: Customer Group name (optional, for filtering accounts)
    """
    # Get rule from DocType
    rule = get_stamp_tax_rule(total, company)

    if not rule:
        return

    # Initialize taxes table if it doesn't exist
    if not doc.taxes:
        doc.taxes = []

    # Handle check stamp
    if rule.get("check_stamp_amount", 0) > 0:
        check_stamp_account = get_tax_account(
            "check_stamp", company, customer_group)
        if check_stamp_account:
            # Check if check stamp row already exists
            found = False
            for tax in doc.taxes:
                if tax.account_head == check_stamp_account:
                    tax.tax_amount = rule["check_stamp_amount"]
                    found = True
                    break

            # Add new check stamp row if not found
            if not found:
                doc.append("taxes", {
                    "add_deduct_tax": "Deduct",
                    "charge_type": "Actual",
                    "account_head": check_stamp_account,
                    "tax_amount": rule["check_stamp_amount"],
                    "description": "دمغة شيك"
                })

    # Handle ATS tax
    if rule.get("ats_tax_amount", 0) > 0:
        # Note: You may need to add ATS tax account to Payment Deductions Accounts
        # For now, we'll skip this or you can add it manually
        pass


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


def calculate_regular_stamp(total, company=None):
    """
    Calculate regular stamp tax (الدمغة العادية) based on rules from Stamp Tax Calculation Rules DocType
    Formula: ((total - subtract_amount) * percentage / 100 + add_amount) / 4

    Args:
        total: Paid amount
        company: Company name (optional, uses default company if not provided)

    Returns:
        float: Regular stamp tax amount
    """
    # Get company if not provided
    if not company:
        company = frappe.defaults.get_global_default("company")

    if not company:
        frappe.throw(_("Company is required to calculate stamp tax"))

    # Get rule from DocType
    rule = get_stamp_tax_rule(total, company)

    if not rule:
        frappe.throw(
            _("No stamp tax calculation rule found for company {0} and amount {1}. Please configure Stamp Tax Calculation Rules.").format(
                company, total
            )
        )

    # Use rule from DocType
    regular_stamp_amount = (
        (total - rule["subtract_amount"]) * rule["percentage"] / 100
        + rule["add_amount"]
    ) / 4

    return regular_stamp_amount


def calculate_additional_stamp(total, company=None):
    """
    Calculate additional stamp tax (الدمغة التدريجية) based on rules from Stamp Tax Calculation Rules DocType
    Formula: regular_stamp_amount * multiplier (from rule)

    Args:
        total: Paid amount
        company: Company name (optional, uses default company if not provided)

    Returns:
        float: Additional stamp tax amount
    """
    # Get company if not provided
    if not company:
        company = frappe.defaults.get_global_default("company")

    if not company:
        frappe.throw(_("Company is required to calculate stamp tax"))

    # Get rule from DocType
    rule = get_stamp_tax_rule(total, company)

    if not rule:
        frappe.throw(
            _("No stamp tax calculation rule found for company {0} and amount {1}. Please configure Stamp Tax Calculation Rules.").format(
                company, total
            )
        )

    # Calculate regular stamp using rule from DocType
    regular_stamp_amount = (
        (total - rule["subtract_amount"]) * rule["percentage"] / 100
        + rule["add_amount"]
    ) / 4

    # Additional stamp = regular stamp * multiplier
    multiplier = rule["additional_stamp_multiplier"]
    additional_stamp_amount = regular_stamp_amount * multiplier

    return additional_stamp_amount


# ============================================================================
# SECTION 3: CONTRACT STAMP HANDLING
# ============================================================================

def handle_contract_stamp(doc, company=None, customer_group=None):
    """
    Handle contract stamp (دمغة عقد) tax row
    Adds or updates contract stamp row based on contract_papers_qty
    Formula: contract_papers_qty * 3 * 0.90

    Args:
        doc: Payment Entry document
        company: Company name
        customer_group: Customer Group name (optional, for filtering accounts)
    """
    contract_account = get_tax_account(
        "contract_stamp", company, customer_group)
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

def handle_vat_20_percent(doc, company=None, customer_group=None):
    """
    Add VAT 20% tax row if Sales Invoice has VAT tax
    Formula: tax_inv.tax_amount * 0.20

    Args:
        doc: Payment Entry document
        company: Company name
        customer_group: Customer Group name (optional, for filtering accounts)
    """
    vat_20_account = get_tax_account("vat_20_percent", company, customer_group)
    vat_tax_account = get_tax_account("vat_tax", company, customer_group)

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

    # Get customer_group from custom field (for filtering accounts)
    customer_group = getattr(doc, "custom_customer_group", None)

    # Handle contract stamp first (works even if taxes table is empty)
    handle_contract_stamp(doc, company, customer_group)

    # Initialize taxes table if it doesn't exist
    if not doc.taxes:
        doc.taxes = []

    total = flt(doc.paid_amount or 0)

    # Calculate commercial profits tax
    calculate_commercial_profits_tax(doc.taxes, total, company, customer_group)

    # Calculate regular stamp tax
    calculate_regular_stamp_tax(doc.taxes, total, company, customer_group)

    # Calculate additional stamp tax
    calculate_additional_stamp_tax(doc.taxes, total, company, customer_group)

    # Handle check stamp and ATS tax from rules
    handle_check_stamp_and_ats_tax(doc, total, company, customer_group)

    # Handle VAT 20%
    handle_vat_20_percent(doc, company, customer_group)


# ============================================================================
# SECTION 6: API METHODS
# ============================================================================

@frappe.whitelist()
def test(total, company=None, customer_group=None):
    """
    API method to calculate tax amounts for Payment Entry
    Called by client script when "Calculate Taxes and Stamps" button is clicked

    Args:
        total: Paid amount (from frappe.form_dict)
        company: Company name (optional, uses default company if not provided)
        customer_group: Customer Group name (optional, used for filtering accounts)

    Returns:
        list: List with dictionary containing calculated tax amounts
    """
    try:
        # Convert total to float
        total = flt(total or 0)

        # Get company if not provided
        if not company:
            company = frappe.defaults.get_global_default("company")

        if not company:
            frappe.throw(_("Company is required"))

        # Calculate tax amounts using rules from DocType
        # Note: customer_group is not used for stamp tax rules (Stamp Tax Calculation Rules only has company)
        # customer_group is only used for filtering accounts (Payment Deductions Accounts has company + customer_group)
        atvat = calculate_commercial_profits(total)
        normal_damgha = calculate_regular_stamp(total, company)
        tadregya_damgha = calculate_additional_stamp(total, company)

        # Return response in expected format
        return [{
            "الارباح التجارية": atvat,
            "الدمغة العادية": normal_damgha,
            "الدمغة التدريجية": tadregya_damgha
        }]

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error in test API method"))
        frappe.throw(_("Error calculating taxes: {0}").format(str(e)))


@frappe.whitelist()
def get_deductions_by_customer_group(company=None, customer_group=None, paid_amount=0):
    """
    Get taxes for Payment Entry based on company and customer_group
    Returns data in Advance Taxes and Charges format (for taxes table)
    Simple calculation: account * percentage * paid_amount

    Args:
        company: Company name (optional, uses default company if not provided)
        customer_group: Customer Group name (required)
        paid_amount: Paid amount to calculate taxes (required)

    Returns:
        list: List of dictionaries with tax rows (Advance Taxes and Charges format)
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_global_default("company")

        if not company:
            frappe.throw(_("Company is required"))

        if not customer_group:
            frappe.throw(_("Customer Group is required"))

        paid_amount = flt(paid_amount or 0)
        if paid_amount <= 0:
            frappe.throw(_("Paid amount must be greater than 0"))

        # Get Payment Deductions Accounts document
        filters = {"company": company, "customer_group": customer_group}
        settings_name = frappe.db.get_value(
            "Payment Deductions Accounts", filters, "name")

        if not settings_name:
            # Return empty list if no settings found (user can configure it)
            return []

        settings = frappe.get_doc("Payment Deductions Accounts", settings_name)

        # Get company cost center
        cost_center = frappe.get_cached_value(
            "Company", company, "cost_center")
        if not cost_center:
            frappe.throw(
                _("Cost Center is not set for company {0}").format(company))

        # Get stamp tax calculation rule from Stamp Tax Calculation Rules
        from payment_taxes_deductions.payment_taxes_deductions.doctype.payment_deductions_accounts.payment_deductions_accounts import (
            get_stamp_tax_rule
        )
        rule = get_stamp_tax_rule(paid_amount, company)

        taxes = []

        # Handle taxes that use Stamp Tax Calculation Rules (complex calculations)
        if rule:
            # Regular stamp tax (دمغة عادية)
            # Formula: ((paid_amount - subtract_amount) * percentage / 100 + add_amount) / 4
            if settings.regular_stamp:
                regular_stamp_amount = (
                    (paid_amount - rule["subtract_amount"]
                     ) * rule["percentage"] / 100
                    + rule["add_amount"]
                ) / 4
                if regular_stamp_amount > 0:
                    account_name = frappe.db.get_value(
                        "Account", settings.regular_stamp, "account_name") or settings.regular_stamp
                    taxes.append({
                        "add_deduct_tax": "Deduct",
                        "charge_type": "Actual",
                        "account_head": settings.regular_stamp,
                        "description": account_name,
                        "cost_center": cost_center,
                        "tax_amount": regular_stamp_amount,
                        "rate": 0,
                    })

            # Additional stamp tax (دمغة اضافية)
            # Formula: regular_stamp_amount * multiplier
            if settings.additional_stamp and regular_stamp_amount > 0:
                multiplier = rule.get("additional_stamp_multiplier", 3)
                additional_stamp_amount = regular_stamp_amount * multiplier
                if additional_stamp_amount > 0:
                    account_name = frappe.db.get_value(
                        "Account", settings.additional_stamp, "account_name") or settings.additional_stamp
                    taxes.append({
                        "add_deduct_tax": "Deduct",
                        "charge_type": "Actual",
                        "account_head": settings.additional_stamp,
                        "description": account_name,
                        "cost_center": cost_center,
                        "tax_amount": additional_stamp_amount,
                        "rate": 0,
                    })

            # Check stamp (دمغة شيك) - fixed amount from rule
            if settings.check_stamp and rule.get("check_stamp_amount", 0) > 0:
                account_name = frappe.db.get_value(
                    "Account", settings.check_stamp, "account_name") or settings.check_stamp
                taxes.append({
                    "add_deduct_tax": "Deduct",
                    "charge_type": "Actual",
                    "account_head": settings.check_stamp,
                    "description": account_name,
                    "cost_center": cost_center,
                    "tax_amount": rule["check_stamp_amount"],
                    "rate": 0,
                })

            # ATS tax (دمغة المهن التطبيقية) - fixed amount from rule
            if settings.applied_professions_tax and rule.get("ats_tax_amount", 0) > 0:
                account_name = frappe.db.get_value(
                    "Account", settings.applied_professions_tax, "account_name") or settings.applied_professions_tax
                taxes.append({
                    "add_deduct_tax": "Deduct",
                    "charge_type": "Actual",
                    "account_head": settings.applied_professions_tax,
                    "description": account_name,
                    "cost_center": cost_center,
                    "tax_amount": rule["ats_tax_amount"],
                    "rate": 0,
                })

        # Handle taxes that use simple percentage from Payment Deductions Accounts
        # Note: Database field names use "_percent" suffix (not "_percentage")
        simple_percentage_fields = [
            ("commercial_profits", "commercial_profits_percent"),
            ("contract_stamp", "contract_stamp_percent"),
            ("medical_professions_tax", "medical_professions_tax_percent"),
            ("vat_20_percent", "vat_20_percent_percent"),
            ("qaderon_difference", "qaderon_difference_percent"),
        ]

        # Loop through simple percentage fields
        for account_field, percentage_field in simple_percentage_fields:
            account = getattr(settings, account_field, None)
            if account:
                # Get percentage (default to 0 if not set)
                percentage = flt(
                    getattr(settings, percentage_field, None) or 0)

                # Calculate amount: paid_amount * (percentage / 100)
                tax_amount = paid_amount * \
                    (percentage / 100) if percentage > 0 else 0

                # Only add if amount > 0 or percentage > 0
                if tax_amount > 0 or percentage > 0:
                    # Get account name for description
                    account_name = frappe.db.get_value(
                        "Account", account, "account_name") or account

                    # Return in Advance Taxes and Charges format (for taxes table)
                    taxes.append({
                        "add_deduct_tax": "Deduct",
                        "charge_type": "Actual",
                        "account_head": account,
                        "description": account_name,
                        "cost_center": cost_center,
                        "tax_amount": tax_amount,
                        "rate": percentage,
                    })

        return taxes

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _(
            "Error getting taxes by customer group"))
        frappe.throw(_("Error getting taxes: {0}").format(str(e)))
