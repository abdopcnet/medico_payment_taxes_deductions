# Payment Taxes Deductions

![Version](https://img.shields.io/badge/version-1.1.2026-blue)

## Overview

Payment Taxes Deductions is a Frappe/ERPNext application that automatically calculates and applies taxes and deductions in Payment Entry documents. The app integrates seamlessly with ERPNext's Payment Entry system to handle various tax calculations including commercial profits tax, stamp taxes, VAT, and withholding taxes.

## Features Preview

### 1. Automatic Tax Calculation
- **Commercial Profits Tax (ارباح تجارية)**: Automatically calculates 1% tax on payments exceeding 300
- **Regular Stamp Tax (دمغة عادية)**: Calculates stamp tax based on configurable rules and ranges
- **Additional Stamp Tax (دمغة اضافية)**: Calculates additional stamp tax as multiplier of regular stamp
- **Contract Stamp Tax (دمغة عقد)**: Handles contract-specific stamp tax calculations
- **VAT 20%**: Calculates VAT at 20% rate when applicable
- **Withholding Tax**: Handles withholding tax deductions

### 2. Configurable Tax Rules
- **Payment Deductions Accounts**: Configure tax accounts per company and customer group
- **Stamp Tax Calculation Rules**: Define calculation rules with percentage, subtract amount, add amount, and multiplier
- **Stamp Tax Ranges**: Configure tax ranges for different payment amounts

### 3. Payment Entry Integration
- **Before Validate Hook**: Automatically calculates taxes before Payment Entry validation
- **Taxes Table Update**: Updates Payment Entry taxes table with calculated amounts
- **Deductions Table Support**: Supports deductions table for withholding taxes and other charges

### 4. API Methods
- `get_deductions_by_customer_group`: Get tax deductions based on company and customer group
- `test`: Test method for tax calculations
- Integration with Payment Entry workflow

### 5. Customer Group Based Configuration
- Different tax accounts per customer group
- Flexible configuration for various business scenarios
- Company-level defaults with customer group overrides

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app payment_taxes_deductions
```

## Configuration

### 1. Payment Deductions Accounts
Configure tax accounts for your company:
- Navigate to: **Payment Deductions Accounts**
- Set up accounts for:
  - Commercial Profits Tax
  - Regular Stamp Tax
  - Additional Stamp Tax
  - Contract Stamp Tax
  - VAT 20%
  - Withholding Tax

### 2. Stamp Tax Calculation Rules
Configure calculation rules:
- Navigate to: **Stamp Tax Calculation Rules**
- Define rules with:
  - Percentage
  - Subtract Amount
  - Add Amount
  - Multiplier (for additional stamp)

### 3. Stamp Tax Ranges
Configure tax ranges:
- Navigate to: **Stamp Tax Range**
- Define ranges for different payment amounts

## Usage

### Automatic Calculation
When creating a Payment Entry:
1. Select payment type (Receive/Pay)
2. Enter party and amount
3. Taxes are automatically calculated based on:
   - Payment amount
   - Company settings
   - Customer group (if configured)
   - Tax rules configured

### Manual Override
You can manually adjust tax amounts in the Payment Entry taxes table if needed.

## Technical Details

### DocTypes
- **Payment Deductions Accounts**: Configuration for tax accounts
- **Stamp Tax Calculation Rules**: Tax calculation rules
- **Stamp Tax Range**: Tax range definitions

### Hooks
- `before_validate` hook on Payment Entry
- Custom JavaScript for Payment Entry form

### API Methods
- `payment_taxes_deductions.payment_taxes_deductions.payment_entry.get_deductions_by_customer_group`
- `payment_taxes_deductions.payment_taxes_deductions.payment_entry.test`

## Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/payment_taxes_deductions
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

## License

mit

## Related Documentation

- [File Structure](app_file_structure.md)
- [API Structure](app_api_tree.md)
- [Workflow Diagram](app_workflow.md)
- [Partly Paid Issue Analysis](partly_paid_issue_analysis.md)
