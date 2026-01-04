# Payment Taxes Deductions - API Structure

## API Methods Overview

This document describes all API methods (whitelisted functions) available in the Payment Taxes Deductions app.

## Base Module

**Module**: `payment_taxes_deductions.payment_taxes_deductions.payment_entry`

## API Methods

### 1. `test()`

**Decorator**: `@frappe.whitelist()`

**Purpose**: Calculate tax amounts for Payment Entry (for testing/display purposes)

**Location**: `payment_taxes_deductions/payment_taxes_deductions/payment_entry.py:434-475`

**Parameters**:
- `total` (float, required): Paid amount to calculate taxes for
- `company` (string, optional): Company name (defaults to global default company)
- `customer_group` (string, optional): Customer Group name (for filtering accounts)

**Returns**:
```python
[
    {
        "الارباح التجارية": float,      # Commercial profits tax amount
        "الدمغة العادية": float,         # Regular stamp tax amount
        "الدمغة التدريجية": float        # Additional stamp tax amount
    }
]
```

**Usage**:
```javascript
frappe.call({
    method: 'payment_taxes_deductions.payment_taxes_deductions.payment_entry.test',
    args: {
        total: 1000,
        company: 'Company Name',
        customer_group: 'Customer Group Name'
    },
    callback: function(r) {
        console.log(r.message);
    }
});
```

**Error Handling**:
- Throws error if company is not provided and no default company exists
- Logs errors to Error Log

---

### 2. `get_deductions_by_customer_group()`

**Decorator**: `@frappe.whitelist()`

**Purpose**: Get taxes for Payment Entry based on company and customer_group
Returns data in Advance Taxes and Charges format (for taxes table)

**Location**: `payment_taxes_deductions/payment_taxes_deductions/payment_entry.py:478-647`

**Parameters**:
- `company` (string, optional): Company name (defaults to global default company)
- `customer_group` (string, required): Customer Group name
- `paid_amount` (float, required): Paid amount to calculate taxes for (must be > 0)

**Returns**:
```python
[
    {
        "add_deduct_tax": "Deduct",
        "charge_type": "Actual",
        "account_head": "Account Name",
        "cost_center": "Cost Center",
        "tax_amount": float,
        "description": "Tax Description"
    },
    # ... more tax rows
]
```

**Usage**:
```javascript
frappe.call({
    method: 'payment_taxes_deductions.payment_taxes_deductions.payment_entry.get_deductions_by_customer_group',
    args: {
        company: 'Company Name',
        customer_group: 'Customer Group Name',
        paid_amount: 1000
    },
    callback: function(r) {
        // r.message contains list of tax rows
        r.message.forEach(function(tax) {
            // Add to Payment Entry taxes table
        });
    }
});
```

**Error Handling**:
- Throws error if company is not provided
- Throws error if customer_group is not provided
- Throws error if paid_amount <= 0
- Throws error if cost center is not set for company
- Returns empty list if no Payment Deductions Accounts found

**Tax Types Calculated**:
1. Regular Stamp Tax (دمغة عادية)
2. Additional Stamp Tax (دمغة اضافية)
3. Commercial Profits Tax (ارباح تجارية) - if amount > 300
4. VAT 20% (if applicable)

---

## Internal Functions (Not API)

### Helper Functions

#### `get_tax_account()`
**Location**: `payment_deductions_accounts.py`
**Purpose**: Get tax account by type, company, and customer group
**Returns**: Account name or None

#### `get_stamp_tax_rule()`
**Location**: `payment_deductions_accounts.py`
**Purpose**: Get stamp tax calculation rule for amount and company
**Returns**: Dictionary with rule details or None

## Hook Functions

### `before_validate()`

**Type**: Document Event Hook
**Location**: `payment_taxes_deductions/payment_taxes_deductions/payment_entry.py:395-427`
**Triggered**: Before Payment Entry validation

**Purpose**: Automatically calculate and update taxes in Payment Entry taxes table

**Process**:
1. Gets company and customer_group
2. Handles contract stamp
3. Initializes taxes table if empty
4. Calculates commercial profits tax
5. Calculates regular stamp tax
6. Calculates additional stamp tax
7. Handles check stamp and ATS tax
8. Handles VAT 20%

**No Return Value**: Updates document in-place

## API Call Flow

### Client to Server

```
Payment Entry Form (JavaScript)
    │
    ├─> test() API Call
    │   └──> payment_entry.py::test()
    │       ├──> calculate_commercial_profits()
    │       ├──> calculate_regular_stamp()
    │       └──> calculate_additional_stamp()
    │
    └─> get_deductions_by_customer_group() API Call
        └──> payment_entry.py::get_deductions_by_customer_group()
            ├──> Payment Deductions Accounts lookup
            ├──> get_stamp_tax_rule()
            └──> Calculate all tax types
```

### Server-Side Hook Flow

```
Payment Entry Document Save
    │
    └─> before_validate() Hook
        └──> payment_entry.py::before_validate()
            ├──> handle_contract_stamp()
            ├──> calculate_commercial_profits_tax()
            ├──> calculate_regular_stamp_tax()
            ├──> calculate_additional_stamp_tax()
            ├──> handle_check_stamp_and_ats_tax()
            └──> handle_vat_20_percent()
                └──> Updates doc.taxes table
```

## Data Structures

### Tax Account Configuration
```python
{
    "company": "Company Name",
    "customer_group": "Customer Group Name",
    "regular_stamp": "Account Name",
    "additional_stamp": "Account Name",
    "commercial_profits": "Account Name",
    "vat_20_percent": "Account Name",
    # ... other tax accounts
}
```

### Stamp Tax Rule
```python
{
    "subtract_amount": float,
    "percentage": float,
    "add_amount": float,
    "multiplier": float  # For additional stamp
}
```

### Tax Row (for taxes table)
```python
{
    "add_deduct_tax": "Deduct",
    "charge_type": "Actual",
    "account_head": "Account Name",
    "cost_center": "Cost Center Name",
    "tax_amount": float,
    "description": "Tax Description"
}
```

## Error Codes and Messages

### Common Errors

1. **Company Required**
   - Message: "Company is required"
   - When: Company not provided and no default company

2. **Customer Group Required**
   - Message: "Customer Group is required"
   - When: `get_deductions_by_customer_group()` called without customer_group

3. **Paid Amount Invalid**
   - Message: "Paid amount must be greater than 0"
   - When: `paid_amount <= 0`

4. **Cost Center Not Set**
   - Message: "Cost Center is not set for company {0}"
   - When: Company has no default cost center

5. **No Stamp Tax Rule**
   - Message: "No stamp tax calculation rule found for company {0} and amount {1}"
   - When: No matching rule in Stamp Tax Calculation Rules

## Security

- All API methods use `@frappe.whitelist()` decorator
- Methods check for required parameters
- Error handling prevents information leakage
- Uses Frappe's permission system

## Performance Considerations

- `get_deductions_by_customer_group()` performs database lookups
- Caching recommended for frequently accessed tax accounts
- Stamp tax rules should be indexed by company and amount range

## Future API Enhancements

Potential new API methods:
- `get_tax_summary()`: Get summary of all applicable taxes
- `validate_tax_configuration()`: Validate tax configuration completeness
- `bulk_calculate_taxes()`: Calculate taxes for multiple payment entries

