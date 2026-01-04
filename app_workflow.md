# Payment Taxes Deductions - Workflow Diagram

## Overview

This document describes the workflow and data flow for the Payment Taxes Deductions app.

## Main Workflow: Payment Entry Tax Calculation

```
┌─────────────────────────────────────────────────────────────────┐
│                    Payment Entry Creation                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              User Enters Payment Details                        │
│  - Payment Type (Receive/Pay)                                  │
│  - Party (Customer/Supplier)                                   │
│  - Paid Amount                                                  │
│  - Company                                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            before_validate() Hook Triggered                     │
│         (payment_entry.py::before_validate())                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Get Company & Customer Group       │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Handle Contract Stamp             │
        │   (if applicable)                   │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Initialize Taxes Table            │
        │   (if empty)                        │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Calculate Commercial Profits Tax  │
        │   (1% if amount > 300)             │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Calculate Regular Stamp Tax      │
        │   (from Stamp Tax Calculation Rules)│
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Calculate Additional Stamp Tax    │
        │   (multiplier of regular stamp)     │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Handle Check Stamp & ATS Tax      │
        │   (from rules)                      │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Handle VAT 20%                    │
        │   (if applicable)                   │
        └─────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Update Payment Entry Taxes Table                   │
│  - Commercial Profits Tax                                       │
│  - Regular Stamp Tax                                            │
│  - Additional Stamp Tax                                         │
│  - VAT 20%                                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Payment Entry Validation & Save                    │
└─────────────────────────────────────────────────────────────────┘
```

## Tax Calculation Flow

### Commercial Profits Tax
```
Paid Amount
    │
    ├─> Is amount > 300?
    │   │
    │   ├─> Yes: Calculate 1% tax
    │   │   └──> Get account from Payment Deductions Accounts
    │   │       └──> Update taxes table
    │   │
    │   └─> No: Skip
    │
    └──> End
```

### Regular Stamp Tax
```
Paid Amount
    │
    ├─> Get Stamp Tax Calculation Rule
    │   └──> Filter by company and amount range
    │
    ├─> Calculate: ((amount - subtract) * percentage / 100 + add) / 4
    │
    ├─> Get account from Payment Deductions Accounts
    │
    └──> Update taxes table
```

### Additional Stamp Tax
```
Regular Stamp Amount
    │
    ├─> Get multiplier from Stamp Tax Calculation Rule
    │
    ├─> Calculate: regular_stamp * multiplier
    │
    ├─> Get account from Payment Deductions Accounts
    │
    └──> Update taxes table
```

## Configuration Workflow

### Payment Deductions Accounts Setup
```
┌─────────────────────────────────────────────────────────────────┐
│         Create Payment Deductions Accounts Document             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Select Company                    │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Select Customer Group (optional)│
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Configure Tax Accounts            │
        │   - Regular Stamp Account           │
        │   - Additional Stamp Account        │
        │   - Commercial Profits Account      │
        │   - VAT 20% Account                 │
        │   - Other tax accounts              │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Save Document                     │
        └─────────────────────────────────────┘
```

### Stamp Tax Calculation Rules Setup
```
┌─────────────────────────────────────────────────────────────────┐
│         Create Stamp Tax Calculation Rules Document            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Select Company                    │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Configure Calculation Parameters  │
        │   - Subtract Amount                 │
        │   - Percentage                      │
        │   - Add Amount                      │
        │   - Multiplier (for additional)     │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Add Stamp Tax Ranges              │
        │   (child table)                     │
        │   - From Amount                     │
        │   - To Amount                       │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Save Document                     │
        └─────────────────────────────────────┘
```

## API Call Workflow

### test() API Method
```
Client Request
    │
    ├─> payment_entry.py::test()
    │   │
    │   ├─> Validate company
    │   │
    │   ├─> calculate_commercial_profits()
    │   │   └──> 1% if amount > 300
    │   │
    │   ├─> calculate_regular_stamp()
    │   │   └──> Get rule → Calculate
    │   │
    │   └─> calculate_additional_stamp()
    │   │       └──> Get rule → Calculate with multiplier
    │   │
    └──> Return JSON response
```

### get_deductions_by_customer_group() API Method
```
Client Request
    │
    ├─> payment_entry.py::get_deductions_by_customer_group()
    │   │
    │   ├─> Validate parameters
    │   │
    │   ├─> Get Payment Deductions Accounts
    │   │   └──> Filter by company + customer_group
    │   │
    │   ├─> Get Stamp Tax Calculation Rule
    │   │   └──> Filter by company + amount
    │   │
    │   ├─> Calculate Regular Stamp Tax
    │   │
    │   ├─> Calculate Additional Stamp Tax
    │   │
    │   ├─> Calculate Commercial Profits Tax
    │   │
    │   ├─> Calculate VAT 20%
    │   │
    └──> Return list of tax rows
```

## Data Flow Diagram

```
┌─────────────────┐
│  Payment Entry  │
└────────┬────────┘
         │
         │ before_validate()
         ▼
┌─────────────────────────────────────┐
│  payment_entry.py                   │
│  - before_validate()                │
│  - calculate_*_tax() functions      │
└────────┬────────────────────────────┘
         │
         │ Uses
         ▼
┌─────────────────────────────────────┐
│  Payment Deductions Accounts         │
│  - get_tax_account()                │
│  - get_stamp_tax_rule()             │
└────────┬────────────────────────────┘
         │
         │ Queries
         ▼
┌─────────────────────────────────────┐
│  Database Tables                    │
│  - tabPayment Deductions Accounts   │
│  - tabStamp Tax Calculation Rules   │
│  - tabStamp Tax Range               │
└─────────────────────────────────────┘
```

## Integration Points

### ERPNext Payment Entry
```
Payment Entry Document
    │
    ├─> Taxes Table (tabPayment Entry Tax)
    │   └──> Updated by before_validate() hook
    │
    ├─> Deductions Table (tabPayment Entry Deduction)
    │   └──> Supported but not auto-calculated
    │
    └─> References Table (tabPayment Entry Reference)
        └──> Used for payment allocation
```

### Customer Group Integration
```
Customer Group
    │
    └─> Used for filtering tax accounts
        └──> Payment Deductions Accounts
            └──> Different accounts per customer group
```

## Error Handling Flow

```
Tax Calculation
    │
    ├─> Missing Configuration?
    │   └──> Skip tax (no error)
    │
    ├─> Missing Company?
    │   └──> Throw error: "Company is required"
    │
    ├─> Missing Cost Center?
    │   └──> Throw error: "Cost Center is not set"
    │
    ├─> No Stamp Tax Rule?
    │   └──> Throw error: "No stamp tax calculation rule found"
    │
    └─> Calculation Error?
        └──> Log error → Throw user-friendly message
```

## State Transitions

### Payment Entry States
```
Draft
    │
    ├─> before_validate() hook
    │   └──> Taxes calculated
    │
    ├─> Save
    │   └──> Taxes persisted
    │
    └─> Submit
        └──> Taxes included in GL entries
```

### Tax Calculation States
```
No Taxes
    │
    ├─> Configuration exists?
    │   │
    │   ├─> Yes: Calculate taxes
    │   │   └──> Taxes Table Updated
    │   │
    │   └─> No: Skip
    │
    └──> End
```

