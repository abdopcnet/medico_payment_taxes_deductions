# Payment Taxes Deductions - File Structure

## Root Directory Structure

```
payment_taxes_deductions/
├── README.md                          # Main documentation
├── app_file_structure.md             # This file
├── app_api_tree.md                   # API structure documentation
├── app_workflow.md                      # Workflow diagram
├── partly_paid_issue_analysis.md     # Deep analysis of payment issues
├── license.txt                        # License file
├── pyproject.toml                     # Python project configuration
└── payment_taxes_deductions/          # Main app directory
```

## Main App Directory Structure

```
payment_taxes_deductions/
├── __init__.py                        # App initialization
├── hooks.py                           # Frappe hooks configuration
├── modules.txt                        # App modules list
├── patches.txt                        # Database patches
├── config/                            # Configuration files
│   └── __init__.py
├── templates/                         # Jinja templates
│   ├── __init__.py
│   └── pages/
│       └── __init__.py
├── public/                            # Public assets
│   └── js/
│       └── payment_entry.js          # Payment Entry client script
└── payment_taxes_deductions/          # Main module
    ├── __init__.py
    └── payment_entry.py              # Payment Entry tax calculations
    └── doctype/                       # Custom DocTypes
        ├── __init__.py
        ├── payment_deductions_accounts/
        │   ├── __init__.py
        │   ├── payment_deductions_accounts.py
        │   ├── payment_deductions_accounts.json
        │   ├── payment_deductions_accounts.js
        │   └── test_payment_deductions_accounts.py
        ├── stamp_tax_calculation_rules/
        │   ├── __init__.py
        │   ├── stamp_tax_calculation_rules.py
        │   ├── stamp_tax_calculation_rules.json
        │   ├── stamp_tax_calculation_rules.js
        │   └── test_stamp_tax_calculation_rules.py
        └── stamp_tax_range/
            ├── __init__.py
            ├── stamp_tax_range.py
            └── stamp_tax_range.json
```

## Key Files Description

### Core Files

#### `payment_taxes_deductions/payment_entry.py`
**Purpose**: Main tax calculation logic for Payment Entry
**Sections**:
1. Tax Calculation Functions (for taxes table)
2. Tax Calculation Functions (for API)
3. Contract Stamp Handling
4. VAT 20% Handling
5. Hook Functions (before_validate)
6. API Methods

**Key Functions**:
- `calculate_commercial_profits_tax()`: Calculates commercial profits tax
- `calculate_regular_stamp_tax()`: Calculates regular stamp tax
- `calculate_additional_stamp_tax()`: Calculates additional stamp tax
- `handle_contract_stamp()`: Handles contract stamp tax
- `handle_vat_20_percent()`: Handles VAT 20% calculation
- `before_validate()`: Hook function called before Payment Entry validation
- `test()`: API method for tax calculation testing
- `get_deductions_by_customer_group()`: API method to get deductions

#### `hooks.py`
**Purpose**: Frappe hooks configuration
**Key Hooks**:
- `doc_events`: Payment Entry before_validate hook
- `doctype_js`: Payment Entry JavaScript file

#### `public/js/payment_entry.js`
**Purpose**: Client-side JavaScript for Payment Entry form
**Functionality**:
- Form event handlers
- Tax calculation triggers
- UI updates

### DocType Files

#### Payment Deductions Accounts
**Path**: `payment_taxes_deductions/doctype/payment_deductions_accounts/`
**Purpose**: Configuration DocType for tax accounts
**Files**:
- `payment_deductions_accounts.py`: Python controller
- `payment_deductions_accounts.json`: DocType definition
- `payment_deductions_accounts.js`: Client script
- `test_payment_deductions_accounts.py`: Unit tests

**Key Methods**:
- `get_tax_account()`: Get tax account by type
- `get_stamp_tax_rule()`: Get stamp tax calculation rule

#### Stamp Tax Calculation Rules
**Path**: `payment_taxes_deductions/doctype/stamp_tax_calculation_rules/`
**Purpose**: Configuration DocType for stamp tax calculation rules
**Files**:
- `stamp_tax_calculation_rules.py`: Python controller
- `stamp_tax_calculation_rules.json`: DocType definition
- `stamp_tax_calculation_rules.js`: Client script
- `test_stamp_tax_calculation_rules.py`: Unit tests

#### Stamp Tax Range
**Path**: `payment_taxes_deductions/doctype/stamp_tax_range/`
**Purpose**: Configuration DocType for stamp tax ranges
**Files**:
- `stamp_tax_range.py`: Python controller
- `stamp_tax_range.json`: DocType definition

## File Relationships

```
hooks.py
  └──> doc_events["Payment Entry"]["before_validate"]
       └──> payment_taxes_deductions/payment_entry.py::before_validate()
            ├──> handle_contract_stamp()
            ├──> calculate_commercial_profits_tax()
            ├──> calculate_regular_stamp_tax()
            ├──> calculate_additional_stamp_tax()
            ├──> handle_check_stamp_and_ats_tax()
            └──> handle_vat_20_percent()
                 └──> payment_deductions_accounts.py::get_tax_account()
                 └──> payment_deductions_accounts.py::get_stamp_tax_rule()

public/js/payment_entry.js
  └──> frappe.call() to payment_entry.py::test()
  └──> frappe.call() to payment_entry.py::get_deductions_by_customer_group()
```

## Database Tables

### Custom DocTypes
- `tabPayment Deductions Accounts`: Tax account configurations
- `tabStamp Tax Calculation Rules`: Tax calculation rules
- `tabStamp Tax Range`: Tax range definitions

### Child Tables
- `tabStamp Tax Range` (child of Stamp Tax Calculation Rules)

## Integration Points

### ERPNext Integration
- **Payment Entry**: Main integration point
  - `tabPayment Entry`: Main document
  - `tabPayment Entry Tax`: Taxes table (updated by app)
  - `tabPayment Entry Deduction`: Deductions table (supported)

### External Dependencies
- **ERPNext Accounts Module**: Payment Entry, Account, Company
- **ERPNext Selling Module**: Customer Group (for filtering)

## Configuration Files

### `modules.txt`
Lists app modules (currently: "Payment Taxes Deductions")

### `patches.txt`
Database migration patches (if any)

### `pyproject.toml`
Python project configuration for pre-commit hooks

## Asset Files

### JavaScript
- `public/js/payment_entry.js`: Client-side Payment Entry enhancements

### No CSS Files
Currently no custom CSS files

## Test Files

- `test_payment_deductions_accounts.py`: Tests for Payment Deductions Accounts
- `test_stamp_tax_calculation_rules.py`: Tests for Stamp Tax Calculation Rules

## Documentation Files

- `README.md`: Main documentation
- `app_file_structure.md`: This file
- `app_api_tree.md`: API structure
- `app_workflow.md`: Workflow diagrams
- `partly_paid_issue_analysis.md`: Deep analysis document

