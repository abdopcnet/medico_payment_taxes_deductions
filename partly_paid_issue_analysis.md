# Deep Analysis: Partly Paid Issue in Payment Entry with Deductions

## Problem Statement

When creating a Payment Entry with:
- **allocated_amount** = 100 in Payment Entry Reference
- **deduction amount** = 14 in Payment Entry Deduction
- **Sales Invoice grand_total** = 114

The Sales Invoice remains **"Partly Paid"** with **outstanding_amount = 14** instead of being fully paid.

## Documents Involved

### 1. Sales Invoice: ACC-SINV-2026-00001
```
- grand_total: 114.00
- outstanding_amount: 14.00
- paid_amount: 0.00
- status: "Partly Paid"
- docstatus: 1 (Submitted)
```

### 2. Payment Entry: ACC-PAY-2026-00001
```
- payment_type: "Receive"
- party: "test"
- paid_amount: 114.00
- received_amount: 114.00
- total_allocated_amount: 100.00
- unallocated_amount: 28.00
- difference_amount: 0.00
- docstatus: 1 (Submitted)
```

### 3. Payment Entry Reference
```
- reference_doctype: "Sales Invoice"
- reference_name: "ACC-SINV-2026-00001"
- allocated_amount: 100.00
- outstanding_amount: 14.00
```

### 4. Payment Entry Deduction
```
- account: "115201 - الخصم تحت حساب الضريبة (Withholding Tax) مدينة -1% مبيعات - M"
- cost_center: "001 - رئيسي - M"
- amount: 14.00
```

### 5. Payment Ledger Entry Records

#### Record 1: Sales Invoice Original Entry
```
- voucher_type: "Sales Invoice"
- voucher_no: "ACC-SINV-2026-00001"
- against_voucher_type: "Sales Invoice"
- against_voucher_no: "ACC-SINV-2026-00001"
- amount: 114.00
- amount_in_account_currency: 114.00
- party_type: "Customer"
- party: "test"
```

#### Record 2: Payment Entry Against Sales Invoice
```
- voucher_type: "Payment Entry"
- voucher_no: "ACC-PAY-2026-00001"
- against_voucher_type: "Sales Invoice"
- against_voucher_no: "ACC-SINV-2026-00001"
- amount: -100.00
- amount_in_account_currency: -100.00
- party_type: "Customer"
- party: "test"
```

#### Record 3: Payment Entry Against Payment Entry (Unallocated)
```
- voucher_type: "Payment Entry"
- voucher_no: "ACC-PAY-2026-00001"
- against_voucher_type: "Payment Entry"
- against_voucher_no: "ACC-PAY-2026-00001"
- amount: -28.00
- amount_in_account_currency: -28.00
- party_type: "Customer"
- party: "test"
```

## Root Cause Analysis

### Problem 1: Allocated Amount Calculation

The **allocated_amount** in Payment Entry Reference is set to **100**, which is the amount directly allocated to the Sales Invoice. However, the **deduction amount of 14** is NOT automatically added to the allocated amount.

**Current Flow:**
1. User sets `allocated_amount = 100` in Payment Entry Reference
2. User adds `deduction amount = 14` in Payment Entry Deduction
3. Payment Entry calculates:
   - `paid_amount = 114`
   - `total_allocated_amount = 100` (only from references, deductions not included)
   - `unallocated_amount = 28` (114 - 100 + 14 deductions = 28)
4. Payment Ledger Entry creates entry: `-100` against Sales Invoice
5. Sales Invoice outstanding: `114 - 100 = 14` (NOT fully paid)

### Problem 2: Deduction Not Part of Allocation

In ERPNext Payment Entry logic:
- **Deductions** are treated as separate accounting entries (expenses/charges)
- **Deductions** are NOT automatically added to the `allocated_amount` for the reference document
- **Deductions** reduce the `unallocated_amount` but don't affect the invoice payment

### Problem 3: Payment Ledger Entry Calculation

The Payment Ledger Entry uses only the `allocated_amount` (100) to create the entry against Sales Invoice, ignoring the deduction amount (14).

**Formula:**
```
Sales Invoice Outstanding = Original Amount - Sum of Allocated Amounts
                          = 114 - 100
                          = 14
```

## Code Analysis

### Payment Entry: `add_party_gl_entries()` Method

**Location:** `erpnext/erpnext/accounts/doctype/payment_entry/payment_entry.py:1305-1394`

```python
for d in self.get("references"):
    allocated_amount_in_company_currency = self.calculate_base_allocated_amount_for_reference(d)
    
    gle.update(
        self.get_gl_dict(
            {
                "account": self.party_account,
                dr_or_cr + "_in_account_currency": d.allocated_amount,  # Uses allocated_amount
                # ...
            }
        )
    )
    
    gle.update(
        {
            "against_voucher_type": d.reference_doctype,  # Sales Invoice
            "against_voucher": d.reference_name,          # Invoice name
        }
    )
    
    gl_entries.append(gle)
```

**Key Finding:**
- Uses `d.allocated_amount` directly for GL entry
- Sets `against_voucher_type` and `against_voucher` to reference the Sales Invoice
- **Only `allocated_amount` is used to pay the invoice**

### Payment Entry: `add_deductions_gl_entries()` Method

**Location:** `erpnext/erpnext/accounts/doctype/payment_entry/payment_entry.py:1653-1675`

```python
def add_deductions_gl_entries(self, gl_entries):
    for d in self.get("deductions"):
        if not d.amount:
            continue
        
        gl_entries.append(
            self.get_gl_dict(
                {
                    "account": d.account,
                    "against": self.party or self.paid_from,  # Against party, NOT invoice
                    "debit_in_account_currency": d.amount,
                    "debit": d.amount,
                    "cost_center": d.cost_center,
                },
                item=d,
            )
        )
```

**Key Finding:**
- Deductions create separate GL entries
- `against` = `self.party` or `self.paid_from` (NOT the invoice)
- **No `against_voucher_type` or `against_voucher`** - deductions are NOT against the invoice
- Deductions are expenses/charges, not payments against the invoice

### Payment Entry: `set_unallocated_amount()` Method

**Location:** `erpnext/erpnext/accounts/doctype/payment_entry/payment_entry.py:1081-1108`

```python
def set_unallocated_amount(self):
    self.unallocated_amount = 0
    if not self.party:
        return

    deductions_to_consider = sum(
        flt(d.amount) for d in self.get("deductions") if not d.is_exchange_gain_loss
    )
    included_taxes = self.get_included_taxes()

    if self.payment_type == "Receive" and self.base_total_allocated_amount < (
        self.base_paid_amount + deductions_to_consider
    ):
        self.unallocated_amount = (
            self.base_paid_amount
            + deductions_to_consider
            - self.base_total_allocated_amount
            - included_taxes
        ) / self.source_exchange_rate
```

**Analysis:**
- Deductions are added to `paid_amount` when calculating `unallocated_amount`
- But deductions are NOT added to `total_allocated_amount`
- This creates the gap: `unallocated_amount = 114 + 14 - 100 = 28`

### Test Case: `test_payment_entry_write_off_difference`

**Location:** `erpnext/erpnext/accounts/doctype/payment_entry/test_payment_entry.py:808-839`

```python
def test_payment_entry_write_off_difference(self):
    si = create_sales_invoice()  # grand_total = 100
    pe = get_payment_entry("Sales Invoice", si.name, bank_account="_Test Cash - _TC")
    pe.received_amount = pe.paid_amount = 95  # Received 95
    pe.append(
        "deductions",
        {"account": "_Test Write Off - _TC", "cost_center": "_Test Cost Center - _TC", "amount": 5},
    )
    pe.save()
    
    # allocated_amount = 100 (full invoice amount)
    # deduction = 5 (write off)
    # paid_amount = 95
    
    pe.submit()
    
    expected_gle = [
        ["Debtors - _TC", 0, 100, si.name],      # Invoice paid 100 (allocated_amount)
        ["_Test Cash - _TC", 95, 0, None],       # Cash received 95
        ["_Test Write Off - _TC", 5, 0, None],   # Write off 5 (NOT against invoice)
    ]
```

**Key Finding:**
- Invoice is paid with `allocated_amount = 100` (full invoice amount)
- Cash received = 95
- Write off (deduction) = 5
- **Deduction is NOT against the invoice** (against_voucher = None)

## Expected vs Actual Behavior

### Expected Behavior
When user sets:
- `allocated_amount = 100`
- `deduction = 14`

The system should:
1. Allocate 100 to Sales Invoice
2. Apply deduction of 14
3. **Total payment against invoice = 114** (100 + 14)
4. Sales Invoice outstanding = 0
5. Sales Invoice status = "Paid"

### Actual Behavior
Current system:
1. Allocates 100 to Sales Invoice
2. Creates separate deduction entry
3. **Total payment against invoice = 100** (deduction not included)
4. Sales Invoice outstanding = 14
5. Sales Invoice status = "Partly Paid"

## Solution: How to Handle This Case

Based on the code analysis, here is the **correct way** to handle the scenario where you receive 100 and want to deduct 1% (or any amount) while making the invoice fully paid:

### Scenario: Receive 100, Invoice = 100, Want to deduct 1% (1)

**WRONG Approach:**
- `paid_amount` = 100
- `allocated_amount` = 99
- `deduction` = 1
- **Result:** Invoice outstanding = 1 (NOT fully paid)

**CORRECT Approach (Based on Code Analysis):**

From the test case `test_payment_entry_write_off_difference`, the correct approach is:

1. **Set `allocated_amount` = Invoice Grand Total** (100 in this case)
2. **Set `paid_amount` = Amount Received** (100 - deduction = 99 in this case)
3. **Add `deduction` = Deduction Amount** (1 in this case)

**Why This Works:**
- `allocated_amount` is used to pay the invoice (see `add_party_gl_entries()` code)
- `deduction` is a separate expense entry (see `add_deductions_gl_entries()` code)
- The equation: `paid_amount + deduction = allocated_amount`
  - 99 + 1 = 100 ✓

**Example:**
```
Sales Invoice grand_total = 100
You receive = 99
Deduction (1%) = 1

Payment Entry:
- paid_amount = 99
- allocated_amount = 100  (full invoice amount)
- deduction amount = 1

GL Entries:
- Debtors: Credit 100 (against Sales Invoice) - Invoice fully paid
- Cash: Debit 99 (received amount)
- Deduction Account: Debit 1 (expense)
```

### Scenario: Receive 100, Invoice = 101, Want to deduct 1% (1.01)

**CORRECT Approach:**
1. **Set `allocated_amount` = Invoice Grand Total** (101)
2. **Set `paid_amount` = Amount Received** (100)
3. **Add `deduction` = Deduction Amount** (1.01)

**But Wait:** This creates `difference_amount = 0.01` which must be zero!

**Solution:** You need to receive **101.01** to cover both the invoice (101) and the deduction (1.01).

**Correct Setup:**
```
Sales Invoice grand_total = 101
You receive = 101.01
Deduction (1% of 101) = 1.01

Payment Entry:
- paid_amount = 101.01
- allocated_amount = 101  (full invoice amount)
- deduction amount = 1.01

GL Entries:
- Debtors: Credit 101 (against Sales Invoice) - Invoice fully paid
- Cash: Debit 101.01 (received amount)
- Deduction Account: Debit 1.01 (expense)

Balance: 101.01 - 101 - 1.01 = 0 ✓
```

### Key Principle from Code Analysis

From `add_party_gl_entries()` and `add_deductions_gl_entries()`:

1. **`allocated_amount`** is the amount used to pay the invoice
2. **`deduction`** is a separate expense entry
3. **The formula must be:**
   ```
   paid_amount = allocated_amount + deduction
   ```
   
   Or equivalently:
   ```
   allocated_amount = paid_amount - deduction
   ```

**For invoice to be fully paid:**
```
allocated_amount = invoice_grand_total
```

**Therefore:**
```
paid_amount = invoice_grand_total + deduction
```

## Practical Example

**Case:** Invoice = 114, You receive 100, Want to deduct 14

**Solution:**
```
Sales Invoice grand_total = 114
Amount you want to receive = 100
Deduction amount = 14

Payment Entry:
- paid_amount = 114  (100 received + 14 deduction)
- allocated_amount = 114  (full invoice amount)
- deduction amount = 14

GL Entries:
- Debtors: Credit 114 (against Sales Invoice) - Invoice fully paid
- Cash: Debit 100 (actually received)
- Deduction Account: Debit 14 (expense)

Wait: This doesn't balance! 114 ≠ 100 + 14

CORRECT Solution:
Since you only received 100, you need to set:
- paid_amount = 114  (to cover invoice + deduction)
- allocated_amount = 114  (to pay full invoice)
- deduction = 14

But this means you need to receive 114, not 100!

ALTERNATIVE: If you only received 100:
- paid_amount = 100
- allocated_amount = 100
- deduction = 14 (but this creates difference_amount = 14)

THIS WON'T WORK because difference_amount must be zero!

REAL SOLUTION:
You must receive 114 to fully pay the invoice and cover the deduction:
- paid_amount = 114
- allocated_amount = 114
- deduction = 14

Or, if you only received 100:
- paid_amount = 100
- allocated_amount = 100
- deduction = 0 (no deduction possible if you want invoice fully paid)
```

## Conclusion Based on Code Analysis

**From the code in `add_party_gl_entries()` and `add_deductions_gl_entries()`:**

1. **`allocated_amount`** is used directly to pay the invoice (line 1360, 1389-1390)
2. **`deduction`** creates a separate GL entry, NOT against the invoice (line 1667)
3. **To fully pay an invoice:** `allocated_amount = invoice_grand_total`
4. **The accounting equation must balance:** `paid_amount = allocated_amount + deduction`
5. **Therefore:** To fully pay an invoice with a deduction, you must receive: `invoice_grand_total + deduction`

**For your case (Invoice = 114, Want deduction = 14):**
- You must receive: **114 + 14 = 128**
- Set `paid_amount = 128`
- Set `allocated_amount = 114` (full invoice)
- Set `deduction = 14`

**If you only received 100:**
- Set `paid_amount = 100`
- Set `allocated_amount = 100` (invoice will be partly paid)
- Set `deduction = 0` (no deduction possible)

**OR:**
- Set `paid_amount = 114`
- Set `allocated_amount = 114` (invoice fully paid)
- Set `deduction = 14` (but you need to have received 114, not 100)

## Related DocTypes and Child Tables

### Payment Entry
- **Main DocType**: `tabPayment Entry`
- **Child Tables**:
  - `tabPayment Entry Reference` (references)
  - `tabPayment Entry Deduction` (deductions)
  - `tabPayment Entry Tax` (taxes)

### Payment Entry Reference
- **Table**: `tabPayment Entry Reference`
- **Key Fields**:
  - `reference_doctype`: Document type (Sales Invoice, etc.)
  - `reference_name`: Document name
  - `allocated_amount`: Amount allocated to reference (USED TO PAY INVOICE)
  - `outstanding_amount`: Outstanding amount in reference

### Payment Entry Deduction
- **Table**: `tabPayment Entry Deduction`
- **Key Fields**:
  - `account`: Deduction account
  - `cost_center`: Cost center
  - `amount`: Deduction amount (SEPARATE EXPENSE, NOT AGAINST INVOICE)
  - `is_exchange_gain_loss`: Flag for exchange gain/loss

### Payment Ledger Entry
- **Table**: `tabPayment Ledger Entry`
- **Purpose**: Tracks all payment transactions
- **Key Fields**:
  - `voucher_type`: Source document type
  - `voucher_no`: Source document name
  - `against_voucher_type`: Target document type
  - `against_voucher_no`: Target document name
  - `amount`: Transaction amount
  - `amount_in_account_currency`: Amount in account currency

### Sales Invoice
- **Main DocType**: `tabSales Invoice`
- **Key Fields**:
  - `grand_total`: Total invoice amount
  - `outstanding_amount`: Remaining unpaid amount
  - `paid_amount`: Paid amount (for POS invoices only)
  - `status`: Invoice status (Unpaid, Partly Paid, Paid, etc.)

## Data Flow Diagram

```
Payment Entry Creation
    │
    ├─> References Table
    │   └─> allocated_amount = 100
    │
    ├─> Deductions Table
    │   └─> amount = 14
    │
    └─> Calculation
        ├─> paid_amount = 114
        ├─> total_allocated_amount = 100
        └─> unallocated_amount = 28

Payment Entry Submit
    │
    ├─> make_gl_entries()
    │   ├─> add_party_gl_entries()
    │   │   └─> GL Entry: -100 against Sales Invoice (uses allocated_amount)
    │   │
    │   ├─> add_deductions_gl_entries()
    │   │   └─> GL Entry: -14 to Deduction Account (NOT against invoice)
    │   │
    │   └─> add_bank_gl_entries()
    │       └─> GL Entry: +114 to Bank Account
    │
    ├─> update_outstanding_amounts()
    │   └─> Calls set_missing_ref_details()
    │
    └─> Payment Ledger Entry Created
        ├─> Entry 1: -100 against Sales Invoice
        └─> Entry 2: -14 to Deduction Account (not against invoice)

Sales Invoice Update
    │
    └─> update_voucher_outstanding()
        └─> Calculates from Payment Ledger Entry
            └─> outstanding = 114 - 100 = 14
            └─> status = "Partly Paid"
```

## Recommendations

1. **For Users**: Set `allocated_amount = invoice_grand_total` to fully pay invoice. Deduction is separate.
2. **For Developers**: Understand that deductions are expenses, not part of invoice payment
3. **For Accountants**: Review if deduction should be separate expense or part of payment
4. **Documentation**: Update user guide to explain deduction vs allocation behavior
