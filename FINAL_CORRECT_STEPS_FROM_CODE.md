# الخطوات الصحيحة من تحليل الكود الكامل

## تحليل الكود الفعلي

### 1. من `set_total_allocated_amount()` (سطر 1068-1079)

```python
def set_total_allocated_amount(self):
    total_allocated_amount, base_total_allocated_amount = 0, 0
    for d in self.get("references"):
        if d.allocated_amount:
            total_allocated_amount += flt(d.allocated_amount)
            base_total_allocated_amount += self.calculate_base_allocated_amount_for_reference(d)
    
    self.total_allocated_amount = abs(total_allocated_amount)
    self.base_total_allocated_amount = abs(base_total_allocated_amount)
```

**المعنى:** `total_allocated_amount` = مجموع `allocated_amount` من جدول `references`

### 2. من `set_unallocated_amount()` (سطر 1081-1108)

```python
def set_unallocated_amount(self):
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

**المعادلة:**
```
unallocated_amount = (paid_amount + deductions_to_consider - total_allocated_amount - included_taxes) / source_exchange_rate
```

### 3. من `set_difference_amount()` (سطر 1158-1179)

```python
def set_difference_amount(self):
    base_unallocated_amount = flt(self.unallocated_amount) * (
        flt(self.source_exchange_rate) if self.payment_type == "Receive" 
        else flt(self.target_exchange_rate)
    )
    
    base_party_amount = flt(self.base_total_allocated_amount) + flt(base_unallocated_amount)
    included_taxes = self.get_included_taxes()
    
    if self.payment_type == "Receive":
        self.difference_amount = base_party_amount - self.base_received_amount + included_taxes
    
    total_deductions = sum(flt(d.amount) for d in self.get("deductions"))
    
    self.difference_amount = flt(
        self.difference_amount - total_deductions, self.precision("difference_amount")
    )
```

**المعادلة (للـ Receive):**
```
base_unallocated_amount = unallocated_amount * source_exchange_rate
base_party_amount = base_total_allocated_amount + base_unallocated_amount
difference_amount = base_party_amount - base_received_amount + included_taxes - total_deductions
```

### 4. من `add_party_gl_entries()` (سطر 1329-1394)

```python
for d in self.get("references"):
    allocated_amount_in_company_currency = self.calculate_base_allocated_amount_for_reference(d)
    
    gle.update({
        dr_or_cr + "_in_account_currency": d.allocated_amount,  # سطر 1360
        dr_or_cr: allocated_amount_in_company_currency,
        # ...
    })
    
    gle.update({
        "against_voucher_type": d.reference_doctype,  # سطر 1389
        "against_voucher": d.reference_name,          # سطر 1390
    })
    
    gl_entries.append(gle)
```

**المعنى:** `allocated_amount` من جدول `references` يُستخدم مباشرة لإنشاء GL entry ضد الفاتورة

### 5. من `add_deductions_gl_entries()` (سطر 1653-1675)

```python
def add_deductions_gl_entries(self, gl_entries):
    for d in self.get("deductions"):
        if not d.amount:
            continue
        
        gl_entries.append(
            self.get_gl_dict({
                "account": d.account,
                "against": self.party or self.paid_from,  # سطر 1667
                "debit": d.amount,
                # ...
            })
        )
```

**المعنى:** `amount` من جدول `deductions` يُستخدم لإنشاء GL entry منفصل، `against` = `party` (وليس الفاتورة)

### 6. من `on_submit()` (سطر 117-124)

```python
def on_submit(self):
    if self.difference_amount:
        frappe.throw(_("Difference Amount must be zero"))
    self.make_gl_entries()
    self.update_outstanding_amounts()
```

**المعنى:** `difference_amount` يجب أن يكون 0 قبل Submit

## البيانات الفعلية (ACC-PAY-2026-00001 - نجحت)

```
paid_amount = 114
received_amount = 114
total_allocated_amount = 114
unallocated_amount = 4
difference_amount = 0
deductions[0].amount = 4
references[0].allocated_amount = 114
Sales Invoice.status = "Paid"
Sales Invoice.outstanding_amount = 0
```

## الحساب من الكود

### حساب unallocated_amount:

من `set_unallocated_amount()`:
```
unallocated_amount = (paid_amount + deductions_to_consider - total_allocated_amount - included_taxes) / source_exchange_rate
unallocated_amount = (114 + 4 - 114 - 0) / 1 = 4 ✓
```

### حساب difference_amount:

من `set_difference_amount()`:
```
base_unallocated_amount = 4 * 1 = 4
base_party_amount = 114 + 4 = 118
difference_amount = 118 - 114 + 0 - 4 = 0 ✓
```

### GL Entries:

من `add_party_gl_entries()`:
```
GL Entry 1:
- account = party_account (Debtors)
- credit = 114 (allocated_amount)
- against_voucher_type = "Sales Invoice"
- against_voucher_no = "ACC-SINV-2026-00001"
```

من `add_deductions_gl_entries()`:
```
GL Entry 2:
- account = deduction_account
- debit = 4 (deductions[0].amount)
- against = party (وليس الفاتورة)
```

من `add_bank_gl_entries()`:
```
GL Entry 3:
- account = paid_to
- debit = 114 (paid_amount)
```

من `add_party_gl_entries()` (unallocated):
```
GL Entry 4:
- account = party_account
- credit = 4 (unallocated_amount)
- against_voucher_type = "Payment Entry"
- against_voucher_no = "ACC-PAY-2026-00001"
```

## الخطوات الصحيحة (من الكود)

### السيناريو: الفاتورة = 114، استلمت = 110، تريد خصم = 4

### الخطوات:

1. **في Payment Entry - الحقول الأساسية:**

   ```
   payment_type = "Receive"
   paid_amount = 114
   received_amount = 114
   ```

2. **في جدول `references` (Payment Entry Reference):**

   ```
   reference_doctype = "Sales Invoice"
   reference_name = "ACC-SINV-2026-00001"
   allocated_amount = 114  (مبلغ الفاتورة الكامل)
   ```

3. **في جدول `deductions` (Payment Entry Deduction):**

   ```
   account = حساب الخصم
   cost_center = مركز التكلفة
   amount = 4
   ```

4. **النظام سيحسب تلقائياً:**

   من `set_unallocated_amount()`:
   ```
   unallocated_amount = (114 + 4 - 114 - 0) / 1 = 4
   ```

   من `set_difference_amount()`:
   ```
   difference_amount = (114 + 4) - 114 + 0 - 4 = 0
   ```

5. **عند Submit:**

   من `on_submit()`:
   - يتحقق أن `difference_amount = 0` ✓
   - ينشئ GL Entries
   - يستدعي `update_outstanding_amounts()`

6. **النتيجة:**

   من `update_voucher_outstanding()` (في utils.py):
   - يحسب `outstanding_amount` من Payment Ledger Entry
   - `outstanding_amount = 0`
   - `status = "Paid"` ✅

## الخلاصة

**الحقول المطلوبة (من الكود):**

1. `paid_amount` = 114
2. `received_amount` = 114
3. `references[0].allocated_amount` = 114 (مبلغ الفاتورة الكامل)
4. `deductions[0].amount` = 4

**الحقول المحسوبة تلقائياً (من الكود):**

1. `total_allocated_amount` = مجموع `references[].allocated_amount` = 114
2. `unallocated_amount` = `(paid_amount + deductions_to_consider - total_allocated_amount) / source_exchange_rate` = 4
3. `difference_amount` = `(total_allocated_amount + unallocated_amount) - received_amount - total_deductions` = 0

**النتيجة:** الفاتورة مسددة بالكامل ✅

